#!/usr/bin/env python3
"""
Master Corpus Scraper & Builder for Certus Diagnostics Medical Knowledge Base.

Processes all 110 topics across 12 modules in manifest_v1.json:
1. Resolves accurate authoritative URLs for Mayo Clinic, Cleveland Clinic, CDC, ADA, NIDDK, and MedlinePlus.
2. Downloads full raw HTML with browser TLS impersonation (primp) to bypass anti-bot / 403 blocks.
3. Extracts main clinical content (trafilatura / BeautifulSoup).
4. Converts to clean ATX Markdown with YAML metadata headers.
5. Runs quality checks (word count, language, headings, topic keywords).
6. Writes raw HTML, metadata.json (SHA-256, versioning), and clean Markdown into knowledge_base/.
7. Patches manifest_v1.json with direct URLs.
"""

import os
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.downloader import download_html
from scraper.extractor import extract_main_content
from scraper.markdown_converter import convert_to_markdown
from scraper.quality_checker import check_quality
from scraper.metadata_writer import write_metadata
from scraper.search_provider import search_article_urls
from scraper.logger import setup_logger, get_logger, log_job, log_summary

# Canonical verified medical authority URL registry
AUTHORITATIVE_URLS = {
    # Module 1: Diabetes Fundamentals
    "diabetes_overview": {
        "ada": "https://diabetes.org/about-diabetes",
        "cdc": "https://www.cdc.gov/diabetes/about/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes"
    },
    "type1_diabetes": {
        "ada": "https://diabetes.org/about-diabetes/type-1",
        "cdc": "https://www.cdc.gov/diabetes/about/about-type-1-diabetes.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-1-diabetes/symptoms-causes/syc-20353011",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-1-diabetes"
    },
    "type2_diabetes": {
        "ada": "https://diabetes.org/about-diabetes/type-2",
        "cdc": "https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/symptoms-causes/syc-20351193",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes"
    },
    "prediabetes": {
        "cdc": "https://www.cdc.gov/diabetes/prevention-type-2/prediabetes-prevent-type-2.html",
        "ada": "https://diabetes.org/about-diabetes/prediabetes",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/prediabetes/symptoms-causes/syc-20355278",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance"
    },
    "gestational_diabetes": {
        "cdc": "https://www.cdc.gov/diabetes/about/gestational-diabetes.html",
        "ada": "https://diabetes.org/living-with-diabetes/pregnancy/gestational-diabetes",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/gestational-diabetes/symptoms-causes/syc-20355339"
    },
    "insulin": {
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/insulin-medicines-treatments",
        "medlineplus": "https://medlineplus.gov/lab-tests/insulin-in-blood/",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/in-depth/diabetes-treatment/art-20051004"
    },
    "insulin_resistance": {
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance",
        "ada": "https://diabetes.org/health-wellness/medication-treatments",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/metabolic-syndrome/symptoms-causes/syc-20351916"
    },
    "pancreas": {
        "niddk": "https://www.niddk.nih.gov/health-information/digestive-diseases/pancreatitis/definition-facts",
        "medlineplus": "https://medlineplus.gov/pancreaticdiseases.html",
        "cleveland": "https://my.clevelandclinic.org/health/body/21743-pancreas"
    },
    "glucose_metabolism": {
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
        "ada": "https://diabetes.org/about-diabetes",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444"
    },

    # Module 2: Diagnosis & Glycemic Control
    "hba1c": {
        "ada": "https://diabetes.org/about-diabetes/a1c",
        "mayo": "https://www.mayoclinic.org/tests-procedures/hba1c-test/about/pac-20384643",
        "medlineplus": "https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/",
        "cdc": "https://www.cdc.gov/diabetes/managing/managing-blood-sugar/a1c.html",
        "niddk": "https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test"
    },
    "average_blood_glucose": {
        "ada": "https://diabetes.org/about-diabetes/a1c",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/diagnosis-treatment/drc-20371451"
    },
    "fasting_blood_glucose": {
        "ada": "https://diabetes.org/about-diabetes/diagnosis",
        "cdc": "https://www.cdc.gov/diabetes/diabetes-testing/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/diagnosis-treatment/drc-20371451",
        "medlineplus": "https://medlineplus.gov/lab-tests/blood-glucose-test/"
    },
    "random_blood_glucose": {
        "ada": "https://diabetes.org/about-diabetes/diagnosis",
        "medlineplus": "https://medlineplus.gov/lab-tests/blood-glucose-test/",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/diagnosis-treatment/drc-20371451"
    },
    "ogtt": {
        "ada": "https://diabetes.org/about-diabetes/diagnosis",
        "mayo": "https://www.mayoclinic.org/tests-procedures/glucose-tolerance-test/about/pac-20394296",
        "medlineplus": "https://medlineplus.gov/lab-tests/glucose-tolerance-test/"
    },
    "c_peptide": {
        "medlineplus": "https://medlineplus.gov/lab-tests/c-peptide-test/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/24242-c-peptide-test",
        "mayo": "https://www.mayoclinic.org/tests-procedures/c-peptide-test/about/pac-20384646"
    },
    "glucose_monitoring": {
        "ada": "https://diabetes.org/living-with-diabetes/treatment-care/checking-your-blood-sugar",
        "cdc": "https://www.cdc.gov/diabetes/diabetes-testing/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/blood-sugar/art-20046628"
    },
    "postprandial_glucose": {
        "ada": "https://diabetes.org/living-with-diabetes/treatment-care/checking-your-blood-sugar",
        "mayo": "https://www.mayoclinic.org/tests-procedures/blood-sugar-test/about/pac-20385150",
        "cleveland": "https://my.clevelandclinic.org/health/articles/continuous-glucose-monitoring-cgm"
    },

    # Module 3: Kidney & Renal Function
    "creatinine": {
        "niddk": "https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/tests-diagnosis",
        "mayo": "https://www.mayoclinic.org/tests-procedures/creatinine-test/about/pac-20384646",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/urine-albumin-creatinine-ratio",
        "medlineplus": "https://medlineplus.gov/lab-tests/creatinine-test/"
    },
    "egfr": {
        "niddk": "https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/tests-diagnosis",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/urine-albumin-creatinine-ratio",
        "mayo": "https://www.mayoclinic.org/tests-procedures/creatinine-test/about/pac-20384646",
        "medlineplus": "https://medlineplus.gov/lab-tests/estimated-glomerular-filtration-rate-egfr/"
    },
    "bun": {
        "medlineplus": "https://medlineplus.gov/lab-tests/bun-blood-urea-nitrogen/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22020-basic-metabolic-panel-bmp",
        "mayo": "https://www.mayoclinic.org/tests-procedures/creatinine-test/about/pac-20384646"
    },
    "urea": {
        "medlineplus": "https://medlineplus.gov/lab-tests/bun-blood-urea-nitrogen/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/creatinine-test/about/pac-20384646",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22020-basic-metabolic-panel-bmp"
    },
    "urine_creatinine": {
        "medlineplus": "https://medlineplus.gov/lab-tests/creatinine-test/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/urine-albumin-creatinine-ratio",
        "mayo": "https://www.mayoclinic.org/tests-procedures/creatinine-test/about/pac-20384646"
    },
    "microalbumin": {
        "niddk": "https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/tests-diagnosis",
        "ada": "https://diabetes.org/health-wellness/kidney-care",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-nephropathy/diagnosis-treatment/drc-20354562",
        "medlineplus": "https://medlineplus.gov/lab-tests/microalbumin-creatinine-ratio/"
    },
    "albumin_creatinine_ratio": {
        "niddk": "https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/tests-diagnosis",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-nephropathy/diagnosis-treatment/drc-20354562",
        "ada": "https://diabetes.org/health-wellness/kidney-care",
        "medlineplus": "https://medlineplus.gov/lab-tests/microalbumin-creatinine-ratio/"
    },
    "diabetic_kidney_disease": {
        "ada": "https://diabetes.org/health-wellness/kidney-care",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-nephropathy/symptoms-causes/syc-20354556"
    },
    "uric_acid": {
        "medlineplus": "https://medlineplus.gov/lab-tests/uric-acid-test/",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/gout/diagnosis-treatment/drc-20372867",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/17808-hyperuricemia-high-uric-acid-level"
    },
    "electrolytes": {
        "medlineplus": "https://medlineplus.gov/lab-tests/electrolyte-panel/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/comprehensive-metabolic-panel/about/pac-20385006",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22020-basic-metabolic-panel-bmp"
    },

    # Module 5: Lipid Profile
    "lipoprotein_a": {
        "cleveland": "https://my.clevelandclinic.org/health/articles/11920-cholesterol-numbers-what-do-they-mean",
        "mayo": "https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601",
        "medlineplus": "https://medlineplus.gov/lab-tests/lipoprotein-a-blood-test/"
    },

    # Module 6: Vitamins & Micronutrients
    "vitamin_d": {
        "mayo": "https://www.mayoclinic.org/drugs-supplements-vitamin-d/art-20363792",
        "medlineplus": "https://medlineplus.gov/lab-tests/vitamin-d-test/",
        "cleveland": "https://my.clevelandclinic.org/health/articles/15050-vitamin-d-vitamin-d-deficiency"
    },
    "magnesium": {
        "medlineplus": "https://medlineplus.gov/lab-tests/magnesium-blood-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/comprehensive-metabolic-panel/about/pac-20385006",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22020-basic-metabolic-panel-bmp"
    },

    # Module 8: Thyroid Function
    "tsh": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hypothyroidism/diagnosis-treatment/drc-20350289",
        "medlineplus": "https://medlineplus.gov/lab-tests/tsh-thyroid-stimulating-hormone-test/",
        "cleveland": "https://my.clevelandclinic.org/health/articles/23524-thyroid-stimulating-hormone-tsh-levels"
    },
    "t3": {
        "medlineplus": "https://medlineplus.gov/lab-tests/triiodothyronine-t3-tests/",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hyperthyroidism/diagnosis-treatment/drc-20373665",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22425-triiodothyronine-t3"
    },
    "t4": {
        "medlineplus": "https://medlineplus.gov/lab-tests/thyroxine-t4-test/",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hypothyroidism/diagnosis-treatment/drc-20350289",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/17556-thyroid-blood-tests"
    },
    "thyroid_antibodies": {
        "medlineplus": "https://medlineplus.gov/lab-tests/thyroid-antibodies/",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hypothyroidism/diagnosis-treatment/drc-20350289",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/thyroid-antibodies"
    },

    # Module 11: Lifestyle & Self-Management
    "sleep": {
        "cdc": "https://www.cdc.gov/diabetes/php/toolkits/new-beginnings-sleep-health.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/insomnia/symptoms-causes/syc-20355167",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/8718-sleep-apnea"
    },

    # Module 4: Liver Health
    "alt": {
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "medlineplus": "https://medlineplus.gov/lab-tests/alanine-transaminase-alt-test/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22028-alanine-transaminase-alt"
    },
    "ast": {
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22147-aspartate-transferase-ast",
        "medlineplus": "https://medlineplus.gov/lab-tests/ast-test/"
    },
    "bilirubin": {
        "medlineplus": "https://medlineplus.gov/lab-tests/bilirubin-blood-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/bilirubin/about/pac-20393041",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/17845-bilirubin"
    },
    "alp": {
        "medlineplus": "https://medlineplus.gov/lab-tests/alkaline-phosphatase/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22029-alkaline-phosphatase-alp",
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595"
    },
    "ggt": {
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22055-gamma-glutamyl-transferase-ggt-test",
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "medlineplus": "https://medlineplus.gov/lab-tests/gamma-glutamyl-transferase-ggt-test/"
    },
    "albumin": {
        "medlineplus": "https://medlineplus.gov/lab-tests/albumin-blood-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22390-albumin-blood-test"
    },
    "globulin": {
        "medlineplus": "https://medlineplus.gov/lab-tests/globulin-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22390-albumin-blood-test"
    },
    "total_protein": {
        "medlineplus": "https://medlineplus.gov/lab-tests/total-protein-and-albumin-globulin-ag-ratio/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22390-albumin-blood-test"
    },
    "fatty_liver": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/nonalcoholic-fatty-liver-disease/symptoms-causes/syc-20354567",
        "niddk": "https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/15831-fatty-liver-disease"
    },
    "nafld": {
        "niddk": "https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/nonalcoholic-fatty-liver-disease/symptoms-causes/syc-20354567",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-health"
    },
    "liver_function_panel": {
        "medlineplus": "https://medlineplus.gov/lab-tests/liver-function-tests/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/17662-liver-function-tests"
    },

    # Module 5: Lipid Profile
    "hdl": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/in-depth/hdl-cholesterol/art-20046388",
        "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },
    "ldl": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/in-depth/cholesterol/art-20045192",
        "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },
    "total_cholesterol": {
        "cdc": "https://www.cdc.gov/cholesterol/about/index.html",
        "mayo": "https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601",
        "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/"
    },
    "triglycerides": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/in-depth/triglycerides/art-20048186",
        "cleveland": "https://my.clevelandclinic.org/health/articles/11117-triglycerides",
        "medlineplus": "https://medlineplus.gov/lab-tests/triglycerides-test/"
    },
    "vldl": {
        "medlineplus": "https://medlineplus.gov/lab-tests/vldl-cholesterol/",
        "cleveland": "https://my.clevelandclinic.org/health/articles/24540-vldl-cholesterol",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/expert-answers/vldl-cholesterol/faq-20058275"
    },
    "apoa1": {
        "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/",
        "cleveland": "https://my.clevelandclinic.org/health/articles/apolipoprotein-a1",
        "mayo": "https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601"
    },
    "apob": {
        "medlineplus": "https://medlineplus.gov/lab-tests/apolipoprotein-b/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/24992-apolipoprotein-b-test",
        "mayo": "https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601"
    },
    "lipoprotein_a": {
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/21980-lipoprotein-a-test",
        "mayo": "https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601",
        "medlineplus": "https://medlineplus.gov/lab-tests/lipoprotein-a-blood-test/"
    },
    "lipid_panel": {
        "medlineplus": "https://medlineplus.gov/lab-tests/cholesterol-levels/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601",
        "cdc": "https://www.cdc.gov/cholesterol/about/index.html"
    },
    "cholesterol_ratio": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/expert-answers/cholesterol-ratio/faq-20058006",
        "cleveland": "https://my.clevelandclinic.org/health/articles/11920-cholesterol-numbers-what-do-they-mean",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },

    # Module 6: Vitamins & Micronutrients
    "vitamin_d": {
        "mayo": "https://www.mayoclinic.org/drugs-supplements-vitamin-d/art-20363792",
        "medlineplus": "https://medlineplus.gov/lab-tests/vitamin-d-test/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/21112-vitamin-d-deficiency"
    },
    "vitamin_b12": {
        "medlineplus": "https://medlineplus.gov/lab-tests/vitamin-b-test/",
        "mayo": "https://www.mayoclinic.org/drugs-supplements-vitamin-b12/art-20363663",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/22831-vitamin-b12-deficiency"
    },
    "folate": {
        "medlineplus": "https://medlineplus.gov/lab-tests/vitamin-b-test/",
        "mayo": "https://www.mayoclinic.org/drugs-supplements-folate/art-20364625",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/22831-vitamin-b12-deficiency"
    },
    "iron_studies": {
        "medlineplus": "https://medlineplus.gov/lab-tests/iron-tests/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/ferritin-test/about/pac-20384928",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/17820-ferritin-test"
    },
    "magnesium": {
        "medlineplus": "https://medlineplus.gov/lab-tests/magnesium-blood-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/comprehensive-metabolic-panel/about/pac-20385006",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22020-basic-metabolic-panel-bmp"
    },

    # Module 7: Complete Blood Count (CBC)
    "cbc_overview": {
        "medlineplus": "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
    },
    "hemoglobin": {
        "medlineplus": "https://medlineplus.gov/lab-tests/hemoglobin-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/hemoglobin-test/about/pac-20385075",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
    },
    "hematocrit": {
        "medlineplus": "https://medlineplus.gov/lab-tests/hematocrit-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/hematocrit/about/pac-20385282",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
    },
    "rbc": {
        "medlineplus": "https://medlineplus.gov/lab-tests/red-blood-cell-rbc-count/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count",
        "mayo": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919"
    },
    "wbc": {
        "medlineplus": "https://medlineplus.gov/lab-tests/white-blood-cell-wbc-count/",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count",
        "mayo": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919"
    },
    "platelets": {
        "medlineplus": "https://medlineplus.gov/lab-tests/platelet-count/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
    },
    "anemia": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/anemia/symptoms-causes/syc-20351360",
        "medlineplus": "https://medlineplus.gov/anemia.html",
        "niddk": "https://www.niddk.nih.gov/health-information/kidney-disease/anemia"
    },
    "esr": {
        "medlineplus": "https://medlineplus.gov/lab-tests/erythrocyte-sedimentation-rate-esr/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/sed-rate/about/pac-20384797",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/17747-sed-rate-erythrocyte-sedimentation-rate-or-esr-test"
    },
    "crp": {
        "medlineplus": "https://medlineplus.gov/lab-tests/c-reactive-protein-crp-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/c-reactive-protein-test/about/pac-20385228",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/23056-c-reactive-protein-crp-test"
    },

    # Module 8: Thyroid Function
    "tsh": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hypothyroidism/diagnosis-treatment/drc-20350289",
        "medlineplus": "https://medlineplus.gov/lab-tests/tsh-thyroid-stimulating-hormone-test/",
        "cleveland": "https://my.clevelandclinic.org/health/articles/23524-thyroid-stimulating-hormone-tsh-levels"
    },
    "t3": {
        "medlineplus": "https://medlineplus.gov/lab-tests/triiodothyronine-t3-tests/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/thyroid-scan/about/pac-20385202",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/22425-triiodothyronine-t3"
    },
    "t4": {
        "medlineplus": "https://medlineplus.gov/lab-tests/thyroxine-t4-test/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/thyroid-scan/about/pac-20385202",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/17556-thyroid-blood-tests"
    },
    "thyroid_antibodies": {
        "medlineplus": "https://medlineplus.gov/lab-tests/thyroid-antibodies/",
        "mayo": "https://www.mayoclinic.org/tests-procedures/thyroid-scan/about/pac-20385202",
        "cleveland": "https://my.clevelandclinic.org/health/diagnostics/thyroid-antibodies"
    },
    "hypothyroidism": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hypothyroidism/symptoms-causes/syc-20350284",
        "medlineplus": "https://medlineplus.gov/hypothyroidism.html",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/12120-hypothyroidism"
    },
    "hyperthyroidism": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hyperthyroidism/symptoms-causes/syc-20373659",
        "medlineplus": "https://medlineplus.gov/hyperthyroidism.html",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/14129-hyperthyroidism"
    },
    "diabetes_thyroid_connection": {
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-health",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/12120-hypothyroidism"
    },

    # Module 9: Cardiovascular Health
    "heart_disease": {
        "cdc": "https://www.cdc.gov/diabetes/diabetes-complications/diabetes-and-your-heart.html",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart/diabetes-affect-your-heart",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/heart-disease/symptoms-causes/syc-20353118"
    },
    "hypertension": {
        "cdc": "https://www.cdc.gov/high-blood-pressure/about/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/symptoms-causes/syc-20373410",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },
    "stroke": {
        "cdc": "https://www.cdc.gov/stroke/about/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/stroke/symptoms-causes/syc-20350113",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },
    "peripheral_artery_disease": {
        "cleveland": "https://my.clevelandclinic.org/health/diseases/17357-peripheral-artery-disease-pad",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/peripheral-artery-disease/symptoms-causes/syc-20350557"
    },
    "atherosclerosis": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/arteriosclerosis-atherosclerosis/symptoms-causes/syc-20350569",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/16753-atherosclerosis-arterial-disease",
        "medlineplus": "https://medlineplus.gov/atherosclerosis.html"
    },
    "heart_failure": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/heart-failure/symptoms-causes/syc-20373142",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/21494-right-sided-heart-failure",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },

    # Module 10: Diabetes Complications
    "diabetic_neuropathy": {
        "ada": "https://diabetes.org/about-diabetes/complications",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-neuropathy/symptoms-causes/syc-20371580",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies"
    },
    "diabetic_retinopathy": {
        "ada": "https://diabetes.org/health-wellness/eye-health",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-retinopathy/symptoms-causes/syc-20371611",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-eye-disease"
    },
    "diabetic_nephropathy": {
        "ada": "https://diabetes.org/health-wellness/kidney-care",
        "niddk": "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-nephropathy/symptoms-causes/syc-20354556"
    },
    "diabetic_foot": {
        "cdc": "https://www.cdc.gov/diabetes/diabetes-complications/diabetes-and-your-feet.html",
        "ada": "https://diabetes.org/diabetes-and-your-feet",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/amputation-and-diabetes/art-20045762"
    },
    "foot_care": {
        "ada": "https://diabetes.org/diabetes-and-your-feet",
        "cdc": "https://www.cdc.gov/diabetes/diabetes-complications/diabetes-and-your-feet.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/amputation-and-diabetes/art-20045762"
    },
    "diabetic_ketoacidosis": {
        "ada": "https://diabetes.org/about-diabetes/complications",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetic-ketoacidosis/symptoms-causes/syc-20371551",
        "medlineplus": "https://medlineplus.gov/ency/article/000320.htm"
    },
    "hyperosmolar_syndrome": {
        "ada": "https://diabetes.org/about-diabetes/complications",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/21501-type-2-diabetes"
    },
    "hypoglycemia": {
        "ada": "https://diabetes.org/living-with-diabetes/hypoglycemia-low-blood-glucose",
        "cdc": "https://www.cdc.gov/diabetes/signs-symptoms/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hypoglycemia/symptoms-causes/syc-20373685"
    },
    "hyperglycemia": {
        "ada": "https://diabetes.org/about-diabetes/complications",
        "cdc": "https://www.cdc.gov/diabetes/signs-symptoms/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/hyperglycemia/symptoms-causes/syc-20373631"
    },
    "diabetic_skin_conditions": {
        "ada": "https://diabetes.org/about-diabetes/complications",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/21501-type-2-diabetes"
    },
    "dental_health": {
        "ada": "https://diabetes.org/health-wellness/keeping-your-mouth-healthy",
        "cdc": "https://www.cdc.gov/oral-health/about/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/periodontitis/symptoms-causes/syc-20354473"
    },
    "gastroparesis": {
        "niddk": "https://www.niddk.nih.gov/health-information/digestive-diseases/gastroparesis",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/gastroparesis/symptoms-causes/syc-20355787",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/15522-gastroparesis"
    },
    "sexual_dysfunction": {
        "niddk": "https://www.niddk.nih.gov/health-information/urologic-diseases/erectile-dysfunction",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/erectile-dysfunction/symptoms-causes/syc-20355776",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/10035-erectile-dysfunction"
    },
    "infections": {
        "ada": "https://diabetes.org/about-diabetes/complications",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/21501-type-2-diabetes",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444"
    },

    # Module 11: Lifestyle & Self-Management
    "healthy_eating": {
        "ada": "https://diabetes.org/food-nutrition",
        "cdc": "https://www.cdc.gov/diabetes/healthy-eating/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295"
    },
    "carb_counting": {
        "ada": "https://diabetes.org/food-nutrition/understanding-carbs",
        "cdc": "https://www.cdc.gov/diabetes/healthy-eating/index.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295"
    },
    "glycemic_index": {
        "ada": "https://diabetes.org/food-nutrition/understanding-carbs",
        "mayo": "https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/glycemic-index-diet/art-20048478",
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000941.htm"
    },
    "exercise": {
        "cdc": "https://www.cdc.gov/diabetes/living-with/physical-activity.html",
        "ada": "https://diabetes.org/health-wellness/fitness",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-and-exercise/art-20045697"
    },
    "weight_management": {
        "cdc": "https://www.cdc.gov/diabetes/living-with/healthy-weight.html",
        "mayo": "https://www.mayoclinic.org/healthy-lifestyle/weight-loss/in-depth/weight-loss/art-20047752",
        "ada": "https://diabetes.org/health-wellness/weight-management"
    },
    "sleep": {
        "cdc": "https://www.cdc.gov/diabetes/php/toolkits/new-beginnings-sleep-health.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/expert-answers/diabetes-and-sleep/faq-20058474",
        "cleveland": "https://my.clevelandclinic.org/health/diseases/8718-sleep-apnea"
    },
    "smoking": {
        "cdc": "https://www.cdc.gov/diabetes/risk-factors/diabetes-and-smoking.html",
        "ada": "https://diabetes.org/health-wellness/substance-use",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/nicotine-dependence/symptoms-causes/syc-20351584"
    },
    "alcohol": {
        "cdc": "https://www.cdc.gov/alcohol/about-alcohol-use/index.html",
        "ada": "https://diabetes.org/health-wellness/substance-use",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/alcohol-use-disorder/symptoms-causes/syc-20369243"
    },
    "stress_management": {
        "cdc": "https://www.cdc.gov/diabetes/articles/10-tips-coping-diabetes-distress.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/stress-and-diabetes/art-20046037",
        "ada": "https://diabetes.org/health-wellness/mental-health"
    },
    "mental_health": {
        "ada": "https://diabetes.org/health-wellness/mental-health",
        "cdc": "https://www.cdc.gov/diabetes/living-with/mental-health.html",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/depression/symptoms-causes/syc-20356007"
    },
    "hydration": {
        "ada": "https://diabetes.org/food-nutrition",
        "mayo": "https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/water/art-20044256",
        "cleveland": "https://my.clevelandclinic.org/health/treatments/9013-dehydration"
    },

    # Module 12: Medications
    "metformin": {
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000086.htm",
        "mayo": "https://www.mayoclinic.org/drugs-supplements/metformin-oral-route/description/drg-20067074",
        "cleveland": "https://my.clevelandclinic.org/health/drugs/20805-pioglitazone-metformin-extended-release-tablets"
    },
    "insulin_therapy": {
        "ada": "https://diabetes.org/health-wellness/medication-treatments",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/insulin-and-diabetes/art-20046974",
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000082.htm"
    },
    "glp1_agonists": {
        "ada": "https://diabetes.org/health-wellness/medication-treatments",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/expert-answers/byetta/faq-20057955",
        "cleveland": "https://my.clevelandclinic.org/health/treatments/sglt2-inhibitors"
    },
    "sglt2_inhibitors": {
        "ada": "https://diabetes.org/health-wellness/medication-treatments",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/in-depth/diabetes-treatment/art-20051004",
        "cleveland": "https://my.clevelandclinic.org/health/treatments/sglt2-inhibitors"
    },
    "dpp4_inhibitors": {
        "ada": "https://diabetes.org/health-wellness/medication-treatments",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/in-depth/diabetes-treatment/art-20051004",
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000086.htm"
    },
    "sulfonylureas": {
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000086.htm",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/in-depth/diabetes-treatment/art-20051004",
        "cleveland": "https://my.clevelandclinic.org/health/treatments/sulfonylureas"
    },
    "thiazolidinediones": {
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000086.htm",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/in-depth/diabetes-treatment/art-20051004",
        "cleveland": "https://my.clevelandclinic.org/health/drugs/19069-pioglitazone-tablets"
    },
    "statins": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/in-depth/statins/art-20045772",
        "medlineplus": "https://medlineplus.gov/statins.html",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },
    "ace_inhibitors_arbs": {
        "mayo": "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/in-depth/ace-inhibitors/art-20047480",
        "medlineplus": "https://medlineplus.gov/ency/patientinstructions/000099.htm",
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart"
    },
    "aspirin_antiplatelet": {
        "ada": "https://diabetes.org/health-wellness/diabetes-and-your-heart",
        "mayo": "https://www.mayoclinic.org/diseases-conditions/heart-disease/in-depth/daily-aspirin-therapy/art-20046797",
        "cleveland": "https://my.clevelandclinic.org/health/treatments/22282-statins"
    }
}

def resolve_target_url(topic_id, source_key, topic_data, manifest_sources):
    """Resolve the highest-confidence URL for a given topic and medical source."""
    if topic_id in AUTHORITATIVE_URLS and source_key in AUTHORITATIVE_URLS[topic_id]:
        return AUTHORITATIVE_URLS[topic_id][source_key]
    
    direct_urls = topic_data.get("direct_urls", {})
    if source_key in direct_urls and direct_urls[source_key]:
        return direct_urls[source_key]
        
    src_meta = manifest_sources.get(source_key, {})
    query = topic_data.get("queries", {}).get(source_key, topic_data.get("title", ""))
    search_tmpl = src_meta.get("search_url_template", "")
    base_url = src_meta.get("base_url", "")
    keywords = topic_data.get("keywords", [])
    
    if search_tmpl and base_url:
        candidates = search_article_urls(query, base_url, search_tmpl, keywords, max_results=5)
        if candidates:
            return candidates[0]
            
    return None


def run_full_corpus_scrape(force: bool = False, delay: float = 0.2):
    logger = setup_logger()
    logger.info("Starting Full Medical Knowledge Base Corpus Scraper")
    
    manifest_path = ROOT / "manifest_v1.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    sources = manifest.get("sources", {})
    
    total_jobs = 0
    scraped_count = 0
    skipped_count = 0
    failed_count = 0
    start_time = time.time()
    
    for mod in manifest.get("modules", []):
        mod_name = mod.get("module", "")
        mod_folder = mod.get("folder", mod_name)
        
        for topic in mod.get("topics", []):
            topic_id = topic.get("id", "")
            topic_title = topic.get("title", "")
            doc_id = topic.get("document_id", "")
            keywords = topic.get("keywords", []) + [topic_title] + topic.get("clinical_tags", [])
            output_dir = topic.get("output_directory", f"knowledge_base/{mod_folder}/{topic_id}")
            
            queries = topic.get("queries", {})
            if not queries:
                continue
                
            for source_key, query_text in queries.items():
                total_jobs += 1
                source_name = sources.get(source_key, {}).get("name", source_key)
                
                # Check if already scraped
                raw_meta_path = ROOT / output_dir / "raw" / source_key / "metadata.json"
                clean_md_path = ROOT / output_dir / "clean" / source_key / "v1.md"
                
                if not force and raw_meta_path.exists() and clean_md_path.exists():
                    try:
                        with open(raw_meta_path, "r", encoding="utf-8") as mf:
                            mdata = json.load(mf)
                        if mdata.get("status") == "scraped" and mdata.get("word_count", 0) > 100:
                            skipped_count += 1
                            log_job(doc_id, source_key, "SKIPPED", "Already scraped")
                            continue
                    except Exception:
                        pass
                
                # Step 1: Resolve URL
                log_job(doc_id, source_key, "RESOLVING", f"Topic: {topic_title}")
                url = resolve_target_url(topic_id, source_key, topic, sources)
                
                if not url:
                    failed_count += 1
                    log_job(doc_id, source_key, "FAILED", "Could not resolve valid URL")
                    continue
                
                if "direct_urls" not in topic:
                    topic["direct_urls"] = {}
                topic["direct_urls"][source_key] = url
                
                # Step 2: Download raw HTML
                log_job(doc_id, source_key, "DOWNLOADING", f"URL: {url}")
                dl = download_html(url, max_retries=3, delay_seconds=1)
                
                if dl.error or not dl.html:
                    failed_count += 1
                    log_job(doc_id, source_key, "FAILED", f"Download error: {dl.error}")
                    continue
                
                # Step 3: Extract structured clinical content
                log_job(doc_id, source_key, "EXTRACTING")
                extracted_xml = extract_main_content(dl.html)
                if not extracted_xml:
                    failed_count += 1
                    log_job(doc_id, source_key, "FAILED", "Content extraction returned empty")
                    continue
                
                # Step 4: Convert to Markdown
                log_job(doc_id, source_key, "CONVERTING")
                metadata_header = {
                    "title": topic_title,
                    "source": source_name,
                    "url": url,
                }
                markdown_text = convert_to_markdown(extracted_xml, metadata_header)
                
                # Step 5: Quality Check
                log_job(doc_id, source_key, "VALIDATING")
                qresult = check_quality(markdown_text, keywords, module=mod_name)
                
                # Step 6: Write files
                job_info = {
                    "document_id": doc_id,
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "source_key": source_key,
                    "source_name": source_name,
                }
                download_info = {
                    "url": url,
                    "etag": dl.etag,
                    "last_modified": dl.last_modified
                }
                quality_info = {
                    "passed": qresult.passed,
                    "min_words": qresult.min_words,
                    "has_keywords": qresult.has_keywords,
                    "has_headings": qresult.has_headings,
                    "is_english": qresult.is_english,
                    "word_count": qresult.word_count,
                    "reasons": qresult.reasons
                }
                
                abs_out_dir = str(ROOT / output_dir)
                version, has_changed = write_metadata(
                    abs_out_dir,
                    job_info,
                    download_info,
                    quality_info,
                    markdown_text
                )
                
                raw_dir = ROOT / output_dir / "raw" / source_key
                clean_dir = ROOT / output_dir / "clean" / source_key
                raw_dir.mkdir(parents=True, exist_ok=True)
                clean_dir.mkdir(parents=True, exist_ok=True)
                
                raw_file = raw_dir / f"v{version}.html"
                clean_file = clean_dir / f"v{version}.md"
                
                with open(raw_file, "w", encoding="utf-8") as f:
                    f.write(dl.html)
                    
                with open(clean_file, "w", encoding="utf-8") as f:
                    f.write(markdown_text)
                    
                scraped_count += 1
                log_job(
                    doc_id,
                    source_key,
                    "COMPLETED",
                    f"v{version} ({qresult.word_count} words)"
                )
                
                if delay > 0:
                    time.sleep(delay)

    # Update manifest_v1.json with discovered URLs
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    duration = time.time() - start_time
    logger.info("=========================================")
    logger.info("Scraping Run Completed in %.1f seconds", duration)
    logger.info("Total Jobs: %d | Scraped: %d | Skipped: %d | Failed: %d",
                total_jobs, scraped_count, skipped_count, failed_count)
    logger.info("=========================================")
    
    log_summary(total_jobs, scraped_count, skipped_count, failed_count, duration)
    return scraped_count, skipped_count, failed_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run full corpus scraper")
    parser.add_argument("--force", action="store_true", help="Force re-scraping existing files")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between requests")
    args = parser.parse_args()
    
    run_full_corpus_scrape(force=args.force, delay=args.delay)
