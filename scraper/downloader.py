"""
Downloader — HTTP download with retries and metadata extraction.

Downloads raw HTML and captures ETag and Last-Modified headers
for versioning support.
"""

import os
import time
import requests
from dataclasses import dataclass
from typing import Optional
from scraper.logger import get_logger

@dataclass
class DownloadResult:
    html: str
    etag: Optional[str]
    last_modified: Optional[str]
    error: Optional[str] = None

def download_html(url: str, max_retries: int = 3, delay_seconds: int = 2) -> DownloadResult:
    """
    Download HTML from the given URL with retries.
    """
    logger = get_logger()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    for attempt in range(max_retries):
        try:
            # Respect rate limiting
            if attempt > 0:
                time.sleep(delay_seconds)
                
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Check if it's actually HTML
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                return DownloadResult("", None, None, f"Not HTML content: {content_type}")
                
            return DownloadResult(
                html=response.text,
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                error=None
            )
            
        except requests.exceptions.RequestException as e:
            logger.warning("Download attempt %d/%d failed for %s: %s", attempt + 1, max_retries, url, str(e))
            if attempt == max_retries - 1:
                return DownloadResult("", None, None, f"Failed after {max_retries} attempts: {str(e)}")
                
    return DownloadResult("", None, None, "Unknown error")
