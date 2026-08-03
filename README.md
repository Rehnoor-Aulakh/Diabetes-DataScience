Diabetes Research Project using Data Science and NLP

## Research dataset export

Build the V1 research dataset directly from `reports.tests_data`:

```bash
python scripts/build_dataset.py
```

Outputs:

- `data/processed/diabetes_dataset.csv`: one row per report, with selected tests expanded into `<parameter>_value`, `<parameter>_unit`, `<parameter>_reference`, `<parameter>_abnormal`, `<parameter>_category`, `<parameter>_method`, and `<parameter>_technology`.
- `data/processed/diabetes_tests_long.csv`: one row per exported test, useful for grouped EDA by category or parameter.

To include more tests, add their exact `testName` from `reports.tests_data` to `config.py`.
