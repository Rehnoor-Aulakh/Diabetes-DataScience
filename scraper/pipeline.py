"""
Pipeline — Orchestrates the full scraping process for a single job.
"""

import os
import time
from scraper.logger import get_logger, log_job
from scraper.manifest_loader import ScrapeJob
from scraper.search_provider import search_article_urls
from scraper.downloader import download_html
from scraper.extractor import extract_main_content
from scraper.markdown_converter import convert_to_markdown
from scraper.quality_checker import check_quality
from scraper.metadata_writer import write_metadata
from scraper.health_tracker import SourceHealthTracker

SOURCE_CAPABILITIES = {
    "mayo": {"search": False},
    "cleveland": {"search": False},
    "medlineplus": {"search": True},
    "niddk": {"search": True},
    "ada": {"search": True},
    "cdc": {"search": True}
}

health_tracker = SourceHealthTracker()

def run_job(job: ScrapeJob, delay_seconds: int = 2) -> bool:
    """
    Run the full pipeline for a single job.
    Returns True if successful, False otherwise.
    """
    logger = get_logger()
    start_time = time.time()
    
    try:
        if health_tracker.is_disabled(job.source_key):
            log_job(job.document_id, job.source_key, "SKIPPED", "Source is currently disabled due to excessive 403s")
            job.status = "skipped"
            job.error = "Source disabled"
            return False
            
        # Step 1: Search
        if job.direct_url:
            log_job(job.document_id, job.source_key, "SEARCHING", f"Using direct URL: {job.direct_url}")
            urls = [job.direct_url]
        else:
            source_caps = SOURCE_CAPABILITIES.get(job.source_key, {"search": True})
            if not source_caps.get("search", True):
                log_job(job.document_id, job.source_key, "SKIPPED", "Search disabled for provider and no direct URL available")
                job.status = "skipped"
                job.error = "Search disabled"
                return False
                
            log_job(job.document_id, job.source_key, "SEARCHING", f"Query: {job.query}")
            urls = search_article_urls(job.query, job.base_url, job.search_url_template, job.keywords)
        
        if not urls:
            log_job(job.document_id, job.source_key, "FAILED", "Search returned no valid URLs")
            job.status = "failed"
            job.error = "Search failed"
            return False
            
        for url in urls:
            job.url = url
            
            # Step 2: Download
            log_job(job.document_id, job.source_key, "DOWNLOADING", f"URL: {url}")
            download_result = download_html(url, delay_seconds=delay_seconds)
            
            if download_result.error:
                log_job(job.document_id, job.source_key, "FAILED", f"Download error: {download_result.error}")
                if download_result.error == "BLOCKED_403":
                    health_tracker.record_403(job.source_key)
                continue
                
            # Step 3: Extract
            log_job(job.document_id, job.source_key, "EXTRACTING")
            html_content = extract_main_content(download_result.html)
            
            if not html_content:
                log_job(job.document_id, job.source_key, "FAILED", "Could not extract main content")
                continue
                
            # Step 4: Convert to Markdown
            log_job(job.document_id, job.source_key, "CONVERTING")
            metadata_header = {
                "title": job.topic_title,
                "source": job.source_name,
                "url": url,
            }
            markdown_text = convert_to_markdown(html_content, metadata_header)
            
            # Step 5: Quality Check
            log_job(job.document_id, job.source_key, "VALIDATING")
            quality_result = check_quality(markdown_text, job.keywords, job.module)
            
            if not quality_result.passed:
                reasons = ", ".join(quality_result.reasons)
                log_job(job.document_id, job.source_key, "FAILED", f"Quality check failed: {reasons}")
                continue
                
            job.status = "scraped"
            
            # Step 6: Write Files (Raw HTML, Markdown, Metadata)
            job_info = {
                "document_id": job.document_id,
                "topic_id": job.topic_id,
                "topic_title": job.topic_title,
                "source_key": job.source_key,
                "source_name": job.source_name,
            }
            
            download_info = {
                "url": url,
                "etag": download_result.etag,
                "last_modified": download_result.last_modified
            }
            
            quality_info = {
                "passed": quality_result.passed,
                "min_words": quality_result.min_words,
                "has_keywords": quality_result.has_keywords,
                "has_headings": quality_result.has_headings,
                "is_english": quality_result.is_english,
                "word_count": quality_result.word_count,
                "reasons": quality_result.reasons
            }
            
            version, has_changed = write_metadata(
                job.output_directory,
                job_info,
                download_info,
                quality_info,
                markdown_text
            )
            
            # Write actual content files
            raw_dir = os.path.join(job.output_directory, "raw", job.source_key)
            clean_dir = os.path.join(job.output_directory, "clean", job.source_key)
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(clean_dir, exist_ok=True)
            
            raw_path = os.path.join(raw_dir, f"v{version}.html")
            clean_path = os.path.join(clean_dir, f"v{version}.md")
            
            if has_changed or not os.path.exists(raw_path):
                with open(raw_path, 'w', encoding='utf-8') as f:
                    f.write(download_result.html)
                    
            if quality_result.passed:
                if has_changed or not os.path.exists(clean_path):
                    with open(clean_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_text)
                        
            elapsed = time.time() - start_time
            
            if quality_result.passed:
                health_tracker.record_success(job.source_key)
                log_job(
                    job.document_id, 
                    job.source_key, 
                    "COMPLETED", 
                    f"v{version} (new)" if has_changed else f"v{version} (unchanged)",
                    words=quality_result.word_count,
                    duration=f"{elapsed:.1f}s"
                )
                return True
                
        # If we exhausted all URLs and none succeeded
        job.status = "failed"
        job.error = "All found URLs failed quality check or download"
        return False
        
    except Exception as e:
        logger.error("Unexpected error in pipeline for %s (%s): %s", job.document_id, job.source_key, str(e))
        job.status = "failed"
        job.error = f"Unexpected error: {str(e)}"
        return False
