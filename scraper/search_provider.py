"""
Search Provider — Uses the site's own search template to find the article.

Constructs the search URL from the manifest's search_url_template,
downloads the search page, and uses BeautifulSoup to extract the
first internal link that matches the domain.
"""

from urllib.parse import urlparse, quote_plus, urljoin
import requests
from bs4 import BeautifulSoup
from scraper.logger import get_logger

def validate_url(url: str, expected_base_url: str) -> bool:
    """
    Ensure the URL belongs to the expected domain and is an article.
    """
    try:
        if not url.startswith("http"):
            return False
            
        parsed_url = urlparse(url)
        parsed_base = urlparse(expected_base_url)
        
        # Extract domain (e.g., www.diabetes.org -> diabetes.org)
        url_domain = parsed_url.netloc.replace("www.", "")
        base_domain = parsed_base.netloc.replace("www.", "")
        
        # Skip common non-article paths
        bad_paths = ["/search", "/login", "/cart", "/about", "/contact"]
        for bp in bad_paths:
            if parsed_url.path.startswith(bp):
                return False
                
        return url_domain.endswith(base_domain)
    except Exception:
        return False

def search_article_url(query: str, base_url: str, search_url_template: str) -> str | None:
    """
    Search for an article by scraping the site's own search results page.
    Returns the URL if found and valid, otherwise None.
    """
    logger = get_logger()
    
    if not search_url_template:
        logger.error("No search_url_template provided for %s", base_url)
        return None
        
    encoded_query = quote_plus(query)
    search_url = search_url_template.replace("{query}", encoded_query)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml",
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Resolve relative URLs
            if href.startswith('/'):
                href = urljoin(base_url, href)
                
            # Clean up tracking params
            if '?' in href and not href.startswith(search_url.split('?')[0]):
                href = href.split('?')[0]
                
            if validate_url(href, base_url):
                logger.debug("Found valid URL via direct search scrape: %s", href)
                return href
                
        logger.warning("No valid article links found on search page: %s", search_url)
        return None
        
    except Exception as e:
        logger.error("Direct search scrape error for '%s': %s", search_url, str(e))
        return None
