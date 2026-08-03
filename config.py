GLYCEMIC = {
    "HbA1c": "hba1c",
    "AVERAGE BLOOD GLUCOSE (ABG)": "abg",
    "C-PEPTIDE": "c_peptide",
}


RENAL = {
    "CREATININE - SERUM": "creatinine",
    "EST. GLOMERULAR FILTRATION RATE (eGFR)": "egfr",
    "BLOOD UREA NITROGEN (BUN)": "bun",
    "UREA": "urea",
    "URIC ACID": "uric_acid",
    "CALCIUM": "calcium",
    "BUN / SR.CREATININE RATIO": "bun_creatinine_ratio",
    "UREA / SR.CREATININE RATIO": "urea_creatinine_ratio",
    "CREATININE - URINE": "urine_creatinine",
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

