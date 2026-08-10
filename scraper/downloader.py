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
    Download HTML from the given URL with strict, policy-driven retries.
    """
    logger = get_logger()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    NON_RETRY_STATUS = {400, 401, 403, 404, 405, 410, 422, 429}
    
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
                return DownloadResult("", None, None, "NON_HTML_CONTENT")
                
            return DownloadResult(
                html=response.text,
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                error=None
            )
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in NON_RETRY_STATUS:
                error_map = {
                    403: "BLOCKED_403",
                    404: "NOT_FOUND_404",
                    429: "RATE_LIMIT_429"
                }
                error_reason = error_map.get(status_code, f"HTTP_ERROR_{status_code}")
                logger.warning("Download aborted for %s: %s", url, error_reason)
                return DownloadResult("", None, None, error_reason)
            
            logger.warning("Download HTTP error attempt %d/%d for %s: %s", attempt + 1, max_retries, url, str(e))
            if attempt == max_retries - 1:
                return DownloadResult("", None, None, f"SERVER_ERROR_{status_code}")
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.warning("Download connection/timeout attempt %d/%d for %s: %s", attempt + 1, max_retries, url, str(e))
            if attempt == max_retries - 1:
                return DownloadResult("", None, None, "TIMEOUT_OR_CONNECTION_ERROR")
                
        except requests.exceptions.RequestException as e:
            logger.warning("Download unknown error attempt %d/%d for %s: %s", attempt + 1, max_retries, url, str(e))
            if attempt == max_retries - 1:
                return DownloadResult("", None, None, "UNKNOWN_ERROR")
                
    return DownloadResult("", None, None, "UNKNOWN_ERROR")
