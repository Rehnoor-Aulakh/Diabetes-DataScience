"""
Metadata Writer — Generates and updates metadata.json for version control.

Handles content hashing, version incrementing, and writing the metadata file.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from scraper.logger import get_logger

def calculate_hash(content: str) -> str:
    """Calculate SHA-256 hash of text content."""
    return "sha256:" + hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_latest_version(output_dir: str, source_key: str) -> int:
    """Read existing metadata to find the current version."""
    metadata_path = os.path.join(output_dir, "raw", source_key, "metadata.json")
    if not os.path.exists(metadata_path):
        return 0
        
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            return meta.get("version", 0)
    except (json.JSONDecodeError, OSError):
        return 0

def check_content_changed(output_dir: str, source_key: str, new_hash: str) -> bool:
    """Check if the content hash differs from the existing metadata."""
    metadata_path = os.path.join(output_dir, "raw", source_key, "metadata.json")
    if not os.path.exists(metadata_path):
        return True # New content
        
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            return meta.get("content_hash") != new_hash
    except (json.JSONDecodeError, OSError):
        return True

def write_metadata(
    output_dir: str,
    job_info: dict,
    download_info: dict,
    quality_info: dict,
    markdown_content: str
) -> tuple[int, bool]:
    """
    Generate and write metadata.json.
    Returns (version_number, is_new_version).
    """
    logger = get_logger()
    source_key = job_info["source_key"]
    
    # Ensure directories exist
    raw_dir = os.path.join(output_dir, "raw", source_key)
    os.makedirs(raw_dir, exist_ok=True)
    
    content_hash = calculate_hash(markdown_content)
    
    # Version logic
    has_changed = check_content_changed(output_dir, source_key, content_hash)
    current_version = get_latest_version(output_dir, source_key)
    
    if has_changed:
        version = current_version + 1
    else:
        version = current_version
        
    metadata = {
        "document_id": job_info["document_id"],
        "topic": job_info["topic_id"],
        "topic_title": job_info["topic_title"],
        "source": source_key,
        "source_name": job_info["source_name"],
        "version": version,
        "url": download_info.get("url", ""),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "word_count": quality_info.get("word_count", 0),
        "content_hash": content_hash,
        "extractor": "trafilatura/bs4",
        "language": "en",
        "http_etag": download_info.get("etag"),
        "http_last_modified": download_info.get("last_modified"),
        "status": "scraped" if quality_info.get("passed", False) else "failed",
        "quality_checks": {
            "min_words": quality_info.get("min_words", False),
            "has_keywords": quality_info.get("has_keywords", False),
            "has_headings": quality_info.get("has_headings", False),
            "is_english": quality_info.get("is_english", False),
            "passed": quality_info.get("passed", False)
        }
    }
    
    if quality_info.get("reasons"):
        metadata["quality_checks"]["reasons"] = quality_info["reasons"]
        
    # Write metadata
    metadata_path = os.path.join(raw_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    return version, has_changed
