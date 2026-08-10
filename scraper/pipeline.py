"""
Pipeline — Orchestrates the full scraping process for a single job.
"""

import os
import time
from scraper.logger import get_logger, log_job
from scraper.manifest_loader import ScrapeJob
from scraper.search_provider import search_article_url
from scraper.downloader import download_html
from scraper.extractor import extract_main_content
from scraper.markdown_converter import convert_to_markdown
from scraper.quality_checker import check_quality
from scraper.metadata_writer import write_metadata

def run_job(job: ScrapeJob, delay_seconds: int = 2) -> bool:
    """
    Run the full pipeline for a single job.
    Returns True if successful, False otherwise.
    """
    logger = get_logger()
    start_time = time.time()
    
    try:
        # Step 1: Search
        log_job(job.document_id, job.source_key, "SEARCHING", f"Query: {job.query}")
        url = search_article_url(job.query, job.base_url, job.search_url_template)
        
        if not url:
            log_job(job.document_id, job.source_key, "FAILED", "Search returned no valid URLs")
            job.status = "failed"
            job.error = "Search failed"
            return False
            
        job.url = url
        
        # Step 2: Download
        log_job(job.document_id, job.source_key, "DOWNLOADING", f"URL: {url}")
        download_result = download_html(url, delay_seconds=delay_seconds)
        
        if download_result.error:
            log_job(job.document_id, job.source_key, "FAILED", f"Download error: {download_result.error}")
            job.status = "failed"
            job.error = f"Download failed: {download_result.error}"
            return False
            
        # Step 3: Extract
        log_job(job.document_id, job.source_key, "EXTRACTING")
        html_content = extract_main_content(download_result.html)
        
        if not html_content:
            log_job(job.document_id, job.source_key, "FAILED", "Could not extract main content")
            job.status = "failed"
            job.error = "Extraction failed"
            return False
            
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
        quality_result = check_quality(markdown_text, job.keywords)
        
        if not quality_result.passed:
            reasons = ", ".join(quality_result.reasons)
            log_job(job.document_id, job.source_key, "FAILED", f"Quality check failed: {reasons}")
            job.status = "failed"
            job.error = f"Quality check failed: {reasons}"
            # We still write metadata so we know it failed
        else:
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
        if has_changed:
            raw_dir = os.path.join(job.output_directory, "raw", job.source_key)
            clean_dir = os.path.join(job.output_directory, "clean", job.source_key)
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(clean_dir, exist_ok=True)
            
            # Write raw HTML
            with open(os.path.join(raw_dir, f"v{version}.html"), 'w', encoding='utf-8') as f:
                f.write(download_result.html)
                
            # Write clean Markdown (if quality passed)
            if quality_result.passed:
                with open(os.path.join(clean_dir, f"v{version}.md"), 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                    
        elapsed = time.time() - start_time
        
        if quality_result.passed:
            log_job(
                job.document_id, 
                job.source_key, 
                "COMPLETED", 
                f"v{version} (new)" if has_changed else f"v{version} (unchanged)",
                words=quality_result.word_count,
                duration=f"{elapsed:.1f}s"
            )
            return True
        return False
        
    except Exception as e:
        logger.error("Unexpected error in pipeline for %s (%s): %s", job.document_id, job.source_key, str(e))
        job.status = "failed"
        job.error = f"Unexpected error: {str(e)}"
        return False
