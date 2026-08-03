import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CORE_PARAMETERS


PATIENTS_CSV = "data/raw/confidential/patients.csv"
REPORTS_CSV = "data/raw/confidential/reports.csv"

WIDE_OUTPUT_CSV = "data/processed/diabetes_dataset.csv"
LONG_OUTPUT_CSV = "data/processed/diabetes_tests_long.csv"


def load_env():
    if not os.path.exists(".env"):
        return

    with open(".env", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def anonymize(prefix, source_id):
    secret = os.environ["SECRET_KEY"].encode("utf-8")
    digest = hmac.new(secret, str(source_id).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{prefix}_{digest[:12].upper()}"


def calculate_age(dob, report_date):
    dob = pd.to_datetime(dob, errors="coerce")
    report_date = pd.to_datetime(report_date, errors="coerce")

    if pd.isna(dob) or pd.isna(report_date):
        return pd.NA

    age = report_date.year - dob.year
    birthday_not_reached = (report_date.month, report_date.day) < (dob.month, dob.day)
    return age - birthday_not_reached


def parse_numeric(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().replace(",", "")
    match = re.search(r"-?\d+(\.\d+)?", text)

    if not match:
        return pd.NA

    return float(match.group())


load_env()

patients = pd.read_csv(PATIENTS_CSV)
reports = pd.read_csv(REPORTS_CSV)

df = reports.merge(
    patients[["patient_id", "dob", "gender"]],
    on="patient_id",
    how="left",
)

dataset_rows = []
test_rows = []

for _, report in df.iterrows():
    row = {}

    row["research_report_id"] = anonymize("REP", report["report_id"])
    row["research_patient_id"] = anonymize("PAT", report["patient_id"])
    row["age"] = calculate_age(report["dob"], report["report_date"])
    row["gender"] = report["gender"]
    row["report_date"] = str(report["report_date"])[:10]

    try:
        tests = json.loads(report["tests_data"])
    except (TypeError, json.JSONDecodeError):
        tests = []

    for test in tests:
        test_name = test.get("testName")

        if test_name not in CORE_PARAMETERS:
            continue

        column = CORE_PARAMETERS[test_name]
        numeric_value = parse_numeric(test.get("value"))

        row[f"{column}_value"] = numeric_value
        row[f"{column}_unit"] = test.get("unit")
        row[f"{column}_reference"] = test.get("referenceRange")
        row[f"{column}_abnormal"] = test.get("abnormal")
        row[f"{column}_category"] = test.get("category")
        row[f"{column}_method"] = test.get("method")
        row[f"{column}_technology"] = test.get("technology")

        test_rows.append(
            {
                "research_report_id": row["research_report_id"],
                "research_patient_id": row["research_patient_id"],
                "age": row["age"],
                "gender": row["gender"],
                "report_date": row["report_date"],
                "test_name": test_name,
                "column": column,
                "value": numeric_value,
                "value_raw": test.get("value"),
                "unit": test.get("unit"),
                "reference": test.get("referenceRange"),
                "abnormal": test.get("abnormal"),
                "category": test.get("category"),
                "method": test.get("method"),
                "technology": test.get("technology"),
            }
        )

    dataset_rows.append(row)

dataset = pd.DataFrame(dataset_rows)
tests_long = pd.DataFrame(test_rows)

os.makedirs("data/processed", exist_ok=True)

dataset.to_csv(WIDE_OUTPUT_CSV, index=False)
tests_long.to_csv(LONG_OUTPUT_CSV, index=False)

print(f"Saved {len(dataset)} report rows to {WIDE_OUTPUT_CSV}")
print(f"Saved {len(tests_long)} test rows to {LONG_OUTPUT_CSV}")
print(f"Selected {len(CORE_PARAMETERS)} test names from tests_data")
