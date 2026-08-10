"""
Manifest Loader — reads manifest_v1.json and builds a job queue.

Each job is a dataclass containing everything the pipeline needs
to scrape one source for one topic. The loader also implements
resume logic: it checks existing metadata to skip completed jobs.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from scraper.logger import get_logger


@dataclass
class ScrapeJob:
    """A single unit of work: scrape one source for one topic."""
    document_id: str
    topic_id: str
    topic_title: str
    module: str
    folder: str
    source_key: str
    source_name: str
    base_url: str
    search_url_template: str
    query: str
    keywords: list[str]
    priority: int
    output_directory: str
    direct_url: Optional[str] = None
    # Populated during execution
    status: str = "pending"
    url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ManifestData:
    """Parsed manifest with defaults and source registry."""
    version: str
    project: str
    defaults: dict
    sources: dict
    source_priority: list[str]
    corpus_stages: list[str]
    jobs: list[ScrapeJob] = field(default_factory=list)
    total_topics: int = 0
    total_jobs: int = 0


def load_manifest(
    manifest_path: str = "manifest_v1.json",
    module_filter: Optional[str] = None,
    topic_filter: Optional[str] = None,
    max_priority: int = 3,
    include_future: bool = False,
    force: bool = False,
) -> ManifestData:
    """
    Load the manifest and build a flat job queue.

    Args:
        manifest_path:  Path to manifest JSON.
        module_filter:  If set, only load jobs from this module.
        topic_filter:   If set, only load this specific topic ID.
        max_priority:   Only include topics with priority <= this value.
        include_future: If True, include topics with status='future'.
        force:          If True, re-scrape even if metadata exists.

    Returns:
        ManifestData with a flat list of ScrapeJob objects.
    """
    logger = get_logger()

    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    manifest = ManifestData(
        version=raw.get("manifest_version", "unknown"),
        project=raw.get("project", ""),
        defaults=raw.get("defaults", {}),
        sources=raw.get("sources", {}),
        source_priority=raw.get("source_priority", []),
        corpus_stages=raw.get("corpus_stages", []),
    )

    logger.info(
        "Loaded manifest v%s — %s",
        manifest.version,
        manifest.project,
    )

    # Build enabled source set
    enabled_sources = {
        key for key, src in manifest.sources.items()
        if src.get("enabled", True)
    }

    topic_count = 0
    job_count = 0

    for mod in raw.get("modules", []):
        mod_name = mod.get("module", "")
        mod_folder = mod.get("folder", mod_name)

        # Module filter
        if module_filter and mod_name != module_filter:
            continue

        for topic in mod.get("topics", []):
            topic_id = topic.get("id", "")
            priority = topic.get("priority", 99)
            status = topic.get("status", "pending")

            # Topic filter
            if topic_filter and topic_id != topic_filter:
                continue

            # Priority filter
            if priority > max_priority:
                continue

            # Future filter
            if status == "future" and not include_future:
                continue

            topic_count += 1
            queries = topic.get("queries", {})
            output_dir = topic.get("output_directory", "")

            for source_key, query_text in queries.items():
                # Skip disabled sources
                if source_key not in enabled_sources:
                    continue

                source_info = manifest.sources.get(source_key, {})

                # Check if already scraped (resume logic)
                if not force and _is_already_scraped(output_dir, source_key):
                    logger.info(
                        "[%s] [%s] Already scraped — skipping",
                        topic.get("document_id", "?"),
                        source_key,
                    )
                    continue

                direct_urls = topic.get("direct_urls", {})
                
                job = ScrapeJob(
                    document_id=topic.get("document_id", ""),
                    topic_id=topic_id,
                    topic_title=topic.get("title", ""),
                    module=mod_name,
                    folder=mod_folder,
                    source_key=source_key,
                    source_name=source_info.get("name", source_key),
                    base_url=source_info.get("base_url", ""),
                    search_url_template=source_info.get("search_url_template", ""),
                    query=query_text,
                    direct_url=direct_urls.get(source_key),
                    keywords=topic.get("keywords", []),
                    priority=priority,
                    output_directory=output_dir,
                )
                manifest.jobs.append(job)
                job_count += 1

    # Sort by priority (1 first), then by document_id for deterministic order
    manifest.jobs.sort(key=lambda j: (j.priority, j.document_id, j.source_key))
    manifest.total_topics = topic_count
    manifest.total_jobs = job_count

    logger.info(
        "Job queue: %d jobs across %d topics (filtered from manifest)",
        job_count,
        topic_count,
    )

    return manifest


def _is_already_scraped(output_directory: str, source_key: str) -> bool:
    """
    Check if a source has already been successfully scraped for a topic.

    Looks for metadata.json in the raw/{source}/ directory and checks
    that status is 'scraped' or later in the pipeline.
    """
    metadata_path = os.path.join(output_directory, "raw", source_key, "metadata.json")
    if not os.path.exists(metadata_path):
        return False

    try:
        with open(metadata_path, encoding="utf-8") as f:
            meta = json.load(f)
        completed_statuses = {"scraped", "cleaned", "chunked", "embedded", "verified", "ready"}
        return meta.get("status", "") in completed_statuses
    except (json.JSONDecodeError, OSError):
        return False
