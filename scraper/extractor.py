"""
Extractor — Extracts main article content from raw HTML.

Uses trafilatura as the primary extraction engine, falling back
to BeautifulSoup if trafilatura fails to find main content.
Returns structured HTML (not raw text) so markdownify can parse it later.
"""

import trafilatura
from bs4 import BeautifulSoup
from scraper.logger import get_logger

def extract_main_content(html: str) -> str | None:
    """
    Extract the main article content from HTML, keeping headings, paragraphs,
    lists, and tables. Removes ads, navigation, and footers.
    
    Returns the extracted content as HTML to preserve structure for markdown conversion.
    """
    logger = get_logger()
    
    if not html or not html.strip():
        return None
        
    try:
        # Trafilatura is excellent at finding main content
        # We output XML/HTML format so we don't lose structure (headings, lists)
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_images=False,
            include_links=False,
            output_format='xml' # XML output preserves structure better than txt
        )
        
        if extracted:
            return extracted
            
        # Fallback to BeautifulSoup if Trafilatura returns None
        logger.debug("Trafilatura failed to extract content, falling back to BeautifulSoup")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove common non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
            tag.decompose()
            
        # Try to find common main content containers
        main_content = None
        for selector in ['main', 'article', '.main-content', '#main-content', '.article-body', '.post-content']:
            found = soup.select_one(selector)
            if found:
                main_content = found
                break
                
        if main_content:
            return str(main_content)
            
        # If no main container found, just return the body
        if soup.body:
            return str(soup.body)
            
        return None
        
    except Exception as e:
        logger.error("Extraction error: %s", str(e))
        return None
