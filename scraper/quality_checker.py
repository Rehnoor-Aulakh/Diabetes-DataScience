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

def check_quality(markdown_text: str, keywords: list[str], min_words: int = 300) -> QualityResult:
    """
    Validate the scraped Markdown content against quality rules.
    """
    logger = get_logger()
    
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
        # Detect on a substring to be faster, avoid markdown symbols
        clean_sample = re.sub(r'#|\*|-', '', text_only[:2000]).strip()
        if clean_sample:
            lang = detect(clean_sample)
            pass_lang = (lang == 'en')
        else:
            pass_lang = False
    except LangDetectException:
        pass_lang = False
        
    # Keyword check
    pass_keywords = False
    if not keywords:
        pass_keywords = True # Skip if no keywords provided
    else:
        text_lower = text_only.lower()
        # Check if any keyword appears in the text
        for kw in keywords:
            if kw.lower() in text_lower:
                pass_keywords = True
                break
                
    # Headings check
    pass_headings = bool(re.search(r'^#+ ', text_only, re.MULTILINE))
    
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
