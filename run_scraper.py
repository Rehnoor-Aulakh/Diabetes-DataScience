"""
CLI entry point for the medical knowledge base scraper.
"""

import argparse
import time
from scraper.logger import setup_logger, get_logger, log_summary
from scraper.manifest_loader import load_manifest
from scraper.pipeline import run_job

def main():
    parser = argparse.ArgumentParser(description="Medical Knowledge Base Scraper")
    parser.add_argument("--manifest", default="manifest_v1.json", help="Path to manifest JSON")
    parser.add_argument("--module", help="Scrape only specific module")
    parser.add_argument("--topic", help="Scrape only specific topic ID")
    parser.add_argument("--priority", type=int, default=3, help="Max priority to scrape (1-3)")
    parser.add_argument("--dry-run", action="store_true", help="Show jobs without scraping")
    parser.add_argument("--force", action="store_true", help="Re-scrape existing content")
    parser.add_argument("--delay", type=int, default=2, help="Delay between requests")
    
    args = parser.parse_args()
    
    logger = setup_logger()
    logger.info("Starting Scraper CLI")
    
    start_time = time.time()
    
    try:
        manifest = load_manifest(
            manifest_path=args.manifest,
            module_filter=args.module,
            topic_filter=args.topic,
            max_priority=args.priority,
            force=args.force
        )
    except Exception as e:
        logger.error("Failed to load manifest: %s", str(e))
        return
        
    if not manifest.jobs:
        logger.info("No jobs to run. Exiting.")
        return
        
    if args.dry_run:
        logger.info("DRY RUN MODE — Would execute the following jobs:")
        for job in manifest.jobs:
            logger.info("  [%s] %s (%s) — %s", job.document_id, job.topic_id, job.source_key, job.query)
        return
        
    scraped = 0
    skipped = 0
    failed = 0
    
    # Run sequentially for v1
    for job in manifest.jobs:
        success = run_job(job, delay_seconds=args.delay)
        if success:
            scraped += 1
        else:
            failed += 1
            
    duration = time.time() - start_time
    log_summary(len(manifest.jobs), scraped, skipped, failed, duration)

if __name__ == "__main__":
    main()
