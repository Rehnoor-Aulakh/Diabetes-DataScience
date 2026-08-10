"""
Search Provider — Uses the site's own search template to find the article.
"""

from urllib.parse import urlparse, quote_plus, urljoin, parse_qs
import requests
from bs4 import BeautifulSoup
from scraper.logger import get_logger

def validate_url(url: str, expected_base_url: str) -> bool:
    try:
        if not url.startswith("http"):
            return False
            
        parsed_url = urlparse(url)
        parsed_base = urlparse(expected_base_url)
        
        url_domain = parsed_url.netloc.replace("www.", "")
        base_domain = parsed_base.netloc.replace("www.", "")
        
        if not url_domain.endswith(base_domain):
            return False
            
        path = parsed_url.path.lower()
            
        # 1. Reject homepages and very short paths
        if not path or path == '/' or len(path) < 10:
            return False
            
        # 2. Reject non-article utility paths anywhere in the path
        bad_segments = ["search", "login", "cart", "about", "contact", "news", "directory", "departments", "patient-visitor-guide", "/es/", "sitemap"]
        for bs in bad_segments:
            if bs in path:
                return False
                
        # 3. Domain-specific strict path requirements
        if "mayoclinic.org" in url_domain:
            if not any(good in path for good in ["/diseases-conditions/", "/tests-procedures/", "/symptoms/"]):
                return False
            if path in ["/diseases-conditions/", "/tests-procedures/", "/symptoms/"]:
                return False
                
        if "niddk.nih.gov" in url_domain:
            if "/health-information/" not in path:
                return False
            if path == "/health-information/":
                return False
                
        if "clevelandclinic.org" in url_domain:
            if "/health/" not in path:
                return False
            if path == "/health/":
                return False
                
        if "medlineplus.gov" in url_domain:
            if not any(good in path for good in ["/ency/", "/lab-tests/"]):
                return False
            if path in ["/ency/", "/lab-tests/"]:
                return False
                
        if "diabetes.org" in url_domain:
            # Reject top level pages that are just hubs
            if path in ["/food-nutrition", "/health-wellness", "/living-with-diabetes", "/about-diabetes"]:
                return False
                
        return True
    except Exception:
        return False

import re

def normalize_word(word: str) -> str:
    w = word.lower()
    if w.endswith('s') and len(w) > 3:
        w = w[:-1]
    if w.endswith('ic') and len(w) > 4:
        w = w[:-2]
    return w

def get_normalized_tokens(text: str) -> set[str]:
    words = re.findall(r'[a-z0-9]+', text.lower())
    return {normalize_word(w) for w in words}

def score_candidate(candidate: dict, query: str, keywords: list[str]) -> int:
    score = 0
    url = candidate['url']
    title = candidate.get('title', '')
    snippet = candidate.get('snippet', '')
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    slug = path.rstrip('/').split('/')[-1]
    slug_tokens = get_normalized_tokens(slug)
    path_tokens = get_normalized_tokens(path)
    title_tokens = get_normalized_tokens(title)
    snippet_tokens = get_normalized_tokens(snippet)
    
    norm_keywords = [normalize_word(kw) for kw in keywords]
    
    # 1. Keyword match
    for kw in norm_keywords:
        if kw in title_tokens:
            score += 15
        if kw in slug_tokens:
            score += 10
        elif kw in path_tokens:
            score += 5
        if kw in snippet_tokens:
            score += 5
            
    # 2. Query word match
    query_words = get_normalized_tokens(query)
    for qw in query_words:
        if qw in title_tokens:
            score += 4
        if qw in slug_tokens:
            score += 4
        elif qw in path_tokens:
            score += 2
        if qw in snippet_tokens:
            score += 2
            
    # 3. Heuristic path validation
    if any(good in path for good in ["/health/lab-tests/", "/health-information/", "/ency/"]):
        score += 10
    if any(good in path for good in ["/diseases-conditions/", "/tests-procedures/", "/symptoms/", "/diseases/"]):
        score += 5
    if any(bad in path for bad in ["/news/", "/blog/", "/press/", "/about-us/", "/contact/", "17957-cyclosporiasis"]):
        score -= 100
        
    return score

def search_article_urls(query: str, base_url: str, search_url_template: str, keywords: list[str], max_results: int = 20) -> list[str]:
    logger = get_logger()
    
    if not search_url_template:
        logger.error("No search_url_template provided for %s", base_url)
        return []
        
    encoded_query = quote_plus(query)
    search_url = search_url_template.replace("{query}", encoded_query)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml",
    }
    
    candidate_urls = []
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        main_content = soup.find('main') or soup.find('div', id=lambda x: x and 'main' in x.lower()) or soup.find('div', id=lambda x: x and 'content' in x.lower()) or soup
        
        for a_tag in main_content.find_all('a', href=True):
            href = a_tag['href']
            
            title = a_tag.get_text(strip=True)
            parent = a_tag.parent
            snippet = parent.get_text(separator=' ', strip=True) if parent else ""
            
            if "medlineplus" in base_url and "vivisimo" in href and "url=" in href:
                parsed_qs = parse_qs(urlparse(href).query)
                if "url" in parsed_qs:
                    href = parsed_qs["url"][0]
            
            if href.startswith('/'):
                href = urljoin(base_url, href)
                
            if '?' in href and not href.startswith(search_url.split('?')[0]):
                href = href.split('?')[0]
                
            if validate_url(href, base_url):
                if href not in [c['url'] for c in candidate_urls]:
                    candidate_urls.append({'url': href, 'title': title, 'snippet': snippet})
                    if len(candidate_urls) >= max_results:
                        break
                        
        scored_results = []
        for candidate in candidate_urls:
            score = score_candidate(candidate, query, keywords)
            # Minimum threshold of 10 to avoid completely irrelevant alerts
            if score >= 10:
                scored_results.append((score, candidate['url']))
                
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [url for score, url in scored_results]
        
        if not results:
            logger.warning("No highly relevant article links found on search page: %s", search_url)
            
        return results
        
    except requests.exceptions.HTTPError as e:
        logger.error("Direct search scrape HTTP error for '%s': %s", search_url, str(e.response.status_code))
        return []
    except Exception as e:
        logger.error("Direct search scrape error for '%s': %s", search_url, str(e))
        return []
