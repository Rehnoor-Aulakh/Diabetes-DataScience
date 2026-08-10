import json

URL_MAP = {
  "diabetes_overview": {
      "ada": "https://diabetes.org/about-diabetes",
      "cdc": "https://www.cdc.gov/diabetes/basics/index.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes"
  },
  "type1_diabetes": {
      "ada": "https://diabetes.org/about-diabetes/type-1",
      "cdc": "https://www.cdc.gov/diabetes/basics/what-is-type-1-diabetes.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-1-diabetes"
  },
  "type2_diabetes": {
      "ada": "https://diabetes.org/about-diabetes/type-2",
      "cdc": "https://www.cdc.gov/diabetes/basics/type2.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes"
  },
  "prediabetes": {
      "ada": "https://diabetes.org/about-diabetes/prediabetes",
      "cdc": "https://www.cdc.gov/diabetes/basics/prediabetes.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance"
  },
  "hba1c": {
      "ada": "https://diabetes.org/about-diabetes/a1c",
      "cdc": "https://www.cdc.gov/diabetes/managing/managing-blood-sugar/a1c.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test",
      "medlineplus": "https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/"
  },
  "fasting_blood_glucose": {
      "medlineplus": "https://medlineplus.gov/lab-tests/blood-glucose-test/"
  },
  "random_blood_glucose": {
      "medlineplus": "https://medlineplus.gov/lab-tests/blood-glucose-test/"
  },
  "ogtt": {
      "medlineplus": "https://medlineplus.gov/lab-tests/glucose-tolerance-test/"
  },
  "insulin": {
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/insulin-medicines-treatments"
  },
  "insulin_resistance": {
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance"
  },
  "creatinine": {
      "medlineplus": "https://medlineplus.gov/lab-tests/creatinine-test/"
  },
  "egfr": {
      "medlineplus": "https://medlineplus.gov/lab-tests/estimated-glomerular-filtration-rate-egfr/"
  },
  "bun": {
      "medlineplus": "https://medlineplus.gov/lab-tests/bun-blood-urea-nitrogen/"
  },
  "microalbumin": {
      "medlineplus": "https://medlineplus.gov/lab-tests/microalbumin-creatinine-ratio/"
  },
  "albumin_creatinine_ratio": {
      "medlineplus": "https://medlineplus.gov/lab-tests/microalbumin-creatinine-ratio/"
  },
  "diabetic_kidney_disease": {
      "cdc": "https://www.cdc.gov/diabetes/managing/problems/kidney-disease.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease"
  },
  "hdl": {
      "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/"
  },
  "ldl": {
      "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/"
  },
  "total_cholesterol": {
      "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/"
  },
  "triglycerides": {
      "medlineplus": "https://medlineplus.gov/lab-tests/triglycerides-test/"
  },
  "vitamin_d": {
      "medlineplus": "https://medlineplus.gov/lab-tests/vitamin-d-test/"
  },
  "vitamin_b12": {
      "medlineplus": "https://medlineplus.gov/lab-tests/vitamin-b-test/"
  },
  "cbc_overview": {
      "medlineplus": "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/"
  },
  "hemoglobin": {
      "medlineplus": "https://medlineplus.gov/lab-tests/hemoglobin-test/"
  },
  "rbc": {
      "medlineplus": "https://medlineplus.gov/lab-tests/red-blood-cell-rbc-count/"
  },
  "wbc": {
      "medlineplus": "https://medlineplus.gov/lab-tests/white-blood-cell-wbc-count/"
  },
  "platelets": {
      "medlineplus": "https://medlineplus.gov/lab-tests/platelet-count/"
  },
  "tsh": {
      "medlineplus": "https://medlineplus.gov/lab-tests/tsh-thyroid-stimulating-hormone-test/"
  },
  "t3": {
      "medlineplus": "https://medlineplus.gov/lab-tests/t3-test/"
  },
  "t4": {
      "medlineplus": "https://medlineplus.gov/lab-tests/thyroxine-t4-test/"
  },
  "heart_disease": {
      "cdc": "https://www.cdc.gov/diabetes/managing/problems/heart-disease.html",
      "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/heart-disease-stroke"
  },
  "hypertension": {
      "cdc": "https://www.cdc.gov/bloodpressure/about.htm"
  }
}

with open("manifest_v1.json", "r") as f:
    manifest = json.load(f)

for mod in manifest["modules"]:
    for topic in mod["topics"]:
        tid = topic["id"]
        if tid in URL_MAP:
            if "direct_urls" not in topic:
                topic["direct_urls"] = {}
            for source, url in URL_MAP[tid].items():
                topic["direct_urls"][source] = url

with open("manifest_v1.json", "w") as f:
    json.dump(manifest, f, indent=2)

print("Manifest patched with correct direct URLs.")
