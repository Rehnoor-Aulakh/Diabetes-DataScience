"""
Quality Checker — validates scraped markdown content.

Ensures the text meets minimum standards (length, language, structure)
before marking it as successfully scraped.
"""

import re
from dataclasses import dataclass
from langdetect import detect, LangDetectException
from scraper.logger import get_logger

@dataclass
class QualityResult:
    passed: bool
    min_words: bool
    is_english: bool
    has_keywords: bool
    has_headings: bool
    word_count: int
    reasons: list[str]

def get_minimum_words(module: str) -> int:
    lab_test_modules = {"diagnosis", "kidney", "liver", "lipid", "vitamins", "cbc", "thyroid", "cardiovascular"}
    disease_modules = {"diabetes", "complications"}
    medication_modules = {"medications"}
    lifestyle_modules = {"lifestyle"}
    
    if module in lab_test_modules:
        return 70
    elif module in disease_modules:
        return 200
    elif module in medication_modules:
        return 200
    elif module in lifestyle_modules:
        return 150
    else:
        return 150

def check_quality(markdown_text: str, keywords: list[str], module: str = "") -> QualityResult:
    """
    Validate the scraped Markdown content against quality rules.
    """
    logger = get_logger()
    
    min_words = get_minimum_words(module)
    
    if not markdown_text or not markdown_text.strip():
        return QualityResult(False, False, False, False, False, 0, ["Empty content"])
        
    # Word count
    # Strip markdown headers if any to get true word count of content
    text_only = re.sub(r'^---[\s\S]*?---\n', '', markdown_text)
    words = len(text_only.split())
    pass_words = words >= min_words
    
    # Language detection
    pass_lang = False
    try:
        clean_sample = re.sub(r'#|\*|-', '', text_only[:2000]).strip()
        if clean_sample:
            lang = detect(clean_sample)
            pass_lang = (lang == 'en')
        else:
            pass_lang = False
    except LangDetectException:
        # Fallback heuristic: check common english stopwords
        common_en = {"the", "and", "is", "of", "to", "in", "for", "with", "a", "that"}
        sample_words = set(text_only.lower().split()[:100])
        pass_lang = len(common_en & sample_words) >= 3
        
    # Keyword check (flexible normalization)
    pass_keywords = False
    if not keywords:
        pass_keywords = True
    else:
        text_lower = text_only.lower()
        text_clean = re.sub(r'[^a-z0-9\s]', ' ', text_lower)
        for kw in keywords:
            kw_lower = kw.lower()
            kw_clean = re.sub(r'[^a-z0-9\s]', ' ', kw_lower).strip()
            if kw_lower in text_lower or (kw_clean and kw_clean in text_clean):
                pass_keywords = True
                break
            # Also check individual words if multi-word keyword has distinctive medical terms
            kw_parts = [p for p in kw_clean.split() if len(p) > 3 and p not in {"blood", "test", "rate", "count", "panel", "disease", "level", "management"}]
            if any(p in text_clean for p in kw_parts):
                pass_keywords = True
                break
                
    # Headings check (ATX headings #, bold lines **, or HTML headings)
    pass_headings = bool(re.search(r'^(?:#+ |\*\*[^\n]+\*\*$|<h[1-6]>)', text_only, re.MULTILINE))
    
    reasons = []
    if not pass_words: reasons.append(f"Word count too low ({words} < {min_words})")
    if not pass_lang: reasons.append("Language not detected as English")
    if not pass_keywords: reasons.append("No topic keywords found in text")
    if not pass_headings: reasons.append("No markdown headings found")
    
    passed = pass_words and pass_lang and pass_keywords
    
    if not passed:
        logger.debug("Quality check failed: %s", ", ".join(reasons))
        
    return QualityResult(
        passed=passed,
        min_words=pass_words,
        is_english=pass_lang,
        has_keywords=pass_keywords,
        has_headings=pass_headings,
        word_count=words,
        reasons=reasons
    )
