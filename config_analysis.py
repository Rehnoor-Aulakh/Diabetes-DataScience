GLYCEMIC = {
    # Shows average blood sugar long term (2-3 months) and is used to diagnose diabetes and prediabetes. It is also used to monitor how well diabetes is being managed.
    #Can be used to classify normal, prediabetes, and diabetes
    "HbA1c": "hba1c",
    #Converts your HbA1c result into the same units you see on your home glucose meter (mg/dL or mmol/L).
    "AVERAGE BLOOD GLUCOSE (ABG)": "abg",
    # Measures a byproduct made when your body produces insulin. 
    # Shows how much insulin your own pancreas is making.
    # Helps find out if your body still makes insulin (Type 2) or makes little to none (Type 1).
    # Low levels mean low insulin production.
    # Normal or high levels mean normal or high insulin production.
    "C-PEPTIDE": "c_peptide",
    
    #INSULIN:
    # Insulin is a natural hormone made by the pancreas that helps move sugar (glucose) from your blood into your cells for energy.
    # Type 1 Diabetes: The body does not make insulin, so people must take it as medicine every day.
    # Type 2 Diabetes: The body makes insulin but cannot use it well, which is called insulin resistance
    }


RENAL = {
    #  1. Direct Markers of Kidney Function
#     What it measures: A waste product from muscle breakdown filtered out of the blood by the kidneys.
#       Diabetes Context: High blood sugar damages the blood vessels in the kidneys (glomeruli). As kidney function declines, creatinine clearance drops, causing serum creatinine levels in the blood to rise. It is a fundamental marker for staging Chronic Kidney Disease (CKD).
    "CREATININE - SERUM": "creatinine",
    # An estimated rate (in mL/min/1.73m²) of how much blood the kidneys filter per minute, calculated using serum creatinine, age, and biological sex.
    "EST. GLOMERULAR FILTRATION RATE (eGFR)": "egfr",
    # What it measures: Urea is a byproduct of protein breakdown by the liver, excreted by the kidneys. BUN measures the nitrogen content within that urea.
# Diabetes Context: Elevated BUN/Urea levels indicate reduced kidney clearance. In diabetic patients, elevated BUN can also point to dehydration, high protein intake, or acute kidney injury (AKI) from metabolic decompensation.
    "BLOOD UREA NITROGEN (BUN)": "bun",
    
    # 2. Urine & Early-Stage Screening Markers

    "UREA": "urea",
    "URIC ACID": "uric_acid",
    "CALCIUM": "calcium",
    "BUN / SR.CREATININE RATIO": "bun_creatinine_ratio",
    "UREA / SR.CREATININE RATIO": "urea_creatinine_ratio",
    # What it measures: The concentration of creatinine excreted in a spot urine sample.
# Diabetes Context: Used primarily as a normalizing denominator to adjust for how concentrated or dilute the urine sample is.
    "CREATININE - URINE": "urine_creatinine",
    #     What it measures: Trace amounts of albumin (a small blood protein) spilling into the urine.
#   Diabetes Context: This is the gold standard early-warning test for diabetic kidney damage. Healthy kidneys do not allow albumin into urine. Microalbuminuria detects microscopic vessel damage years before serum creatinine or eGFR show any abnormality.
    "URINARY MICROALBUMIN": "urinary_microalbumin",
    "URI. ALBUMIN/CREATININE RATIO (UA/C)": "uacr",
}


LIPID = {
    "TOTAL CHOLESTEROL": "total_cholesterol",
    "HDL CHOLESTEROL - DIRECT": "hdl",
    "LDL CHOLESTEROL - DIRECT": "ldl",
    "VLDL CHOLESTEROL": "vldl",
    "TRIGLYCERIDES": "triglycerides",
    "NON-HDL CHOLESTEROL": "non_hdl",
    "TC/ HDL CHOLESTEROL RATIO": "tc_hdl_ratio",
    "TRIG / HDL RATIO": "trig_hdl_ratio",
    "LDL / HDL RATIO": "ldl_hdl_ratio",
    "HDL / LDL RATIO": "hdl_ldl_ratio",
    "APOLIPOPROTEIN - A1 (APO-A1)": "apo_a1",
    "APOLIPOPROTEIN - B (APO-B)": "apo_b",
    "APO B / APO A1 RATIO (APO B/A1)": "apo_b_apo_a1_ratio",
    "LIPOPROTEIN (A) [LP(A)]": "lipoprotein_a",
}


LIVER = {
    "ALANINE TRANSAMINASE (SGPT)": "alt",
    "ASPARTATE AMINOTRANSFERASE (SGOT )": "ast",
    "SGOT / SGPT RATIO": "ast_alt_ratio",
    "ALKALINE PHOSPHATASE": "alkaline_phosphatase",
    "BILIRUBIN - TOTAL": "bilirubin_total",
    "BILIRUBIN -DIRECT": "bilirubin_direct",
    "BILIRUBIN (INDIRECT)": "bilirubin_indirect",
    "GAMMA GLUTAMYL TRANSFERASE (GGT)": "ggt",
    "PROTEIN - TOTAL": "total_protein",
    "ALBUMIN - SERUM": "albumin",
    "SERUM GLOBULIN": "globulin",
    "SERUM ALB/GLOBULIN RATIO": "albumin_globulin_ratio",
}


THYROID = {
    "TSH - ULTRASENSITIVE": "tsh",
    "TOTAL THYROXINE (T4)": "t4",
    "TOTAL TRIIODOTHYRONINE (T3)": "t3",
    "TSH RECEPTOR ANTIBODIES": "tsh_receptor_antibodies",
}


VITAMINS = {
    "25-OH VITAMIN D (TOTAL)": "vitamin_d",
    "VITAMIN B-12": "vitamin_b12",
}


INFLAMMATION = {
    "HIGH SENSITIVITY C-REACTIVE PROTEIN (HS-CRP)": "hs_crp",
    "C-REACTIVE PROTEIN (CRP)": "crp",
    "ERYTHROCYTE SEDIMENTATION RATE (ESR)": "esr",
}


CBC = {
    "HEMOGLOBIN": "hemoglobin",
    "TOTAL LEUCOCYTE COUNT (WBC)": "wbc",
    "PLATELET COUNT": "platelet_count",
    "Hematocrit (PCV)": "hematocrit",
    "Total RBC": "rbc",
    "Mean Corpuscular Volume (MCV)": "mcv",
    "MEAN CORPUSCULAR VOLUME(MCV)": "mcv",
    "Mean Corpuscular Hemoglobin (MCH)": "mch",
    "MEAN CORPUSCULAR HEMOGLOBIN(MCH)": "mch",
    "MEAN CORP.HEMO.CONC(MCHC)": "mchc",
    "Red Cell Distribution Width (RDW - CV)": "rdw_cv",
    "RED CELL DISTRIBUTION WIDTH (RDW-CV)": "rdw_cv",
    "RED CELL DISTRIBUTION WIDTH - SD(RDW-SD)": "rdw_sd",
    "Red Cell Distribution Width - SD (RDW-SD)": "rdw_sd",
    "Mean Platelet Volume (MPV)": "mpv",
    "MEAN PLATELET VOLUME(MPV)": "mpv",
}


CORE_PARAMETERS = {
    **GLYCEMIC,
    **RENAL,
    **LIPID,
    **LIVER,
    **THYROID,
    **VITAMINS,
    **INFLAMMATION,
    **CBC,
}

