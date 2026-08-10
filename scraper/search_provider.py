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

def search_article_urls(query: str, base_url: str, search_url_template: str, max_results: int = 5) -> list[str]:
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
    
    results = []
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Focus on main content to avoid extracting links from the global navigation menu
        main_content = soup.find('main') or soup.find('div', id=lambda x: x and 'main' in x.lower()) or soup.find('div', id=lambda x: x and 'content' in x.lower()) or soup
        
        for a_tag in main_content.find_all('a', href=True):
            href = a_tag['href']
            
            # Handle MedlinePlus redirects
            if "medlineplus" in base_url and "vivisimo" in href and "url=" in href:
                parsed_qs = parse_qs(urlparse(href).query)
                if "url" in parsed_qs:
                    href = parsed_qs["url"][0]
            
            # Resolve relative URLs
            if href.startswith('/'):
                href = urljoin(base_url, href)
                
            # Clean up tracking params
            if '?' in href and not href.startswith(search_url.split('?')[0]):
                href = href.split('?')[0]
                
            if validate_url(href, base_url):
                if href not in results:
                    results.append(href)
                    if len(results) >= max_results:
                        break
                        
        if not results:
            logger.warning("No valid article links found on search page: %s", search_url)
            
        return results
        
    except Exception as e:
        logger.error("Direct search scrape error for '%s': %s", search_url, str(e))
        return []
