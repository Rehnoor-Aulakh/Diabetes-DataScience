"""
Structured logging for the scraper pipeline.

Every log entry includes: timestamp, level, document_id, source, message.
Outputs to both console and a rotating log file.
"""

import logging
import os
import sys
from datetime import datetime, timezone


LOG_FORMAT = "[%(asctime)s] [%(levelname)-7s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Custom formatter that uses UTC
class _UTCFormatter(logging.Formatter):
    converter = lambda *args: datetime.now(timezone.utc).timetuple()


def setup_logger(
    log_dir: str = "knowledge_base/logs",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Create and configure the scraper logger.

    Returns the root 'scraper' logger with both console and file handlers.
    """
    logger = logging.getLogger("scraper")

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = _UTCFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"scraper_{timestamp}.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logger initialized → %s", log_path)
    return logger


def get_logger() -> logging.Logger:
    """Get the scraper logger (must call setup_logger first)."""
    return logging.getLogger("scraper")


def log_job(
    document_id: str,
    source: str,
    status: str,
    message: str = "",
    **extras,
) -> None:
    """
    Log a structured job event.

    Example output:
        [2026-08-10 06:30:00] [INFO   ] [KB-000010] [ada] Downloaded — 4217 words, 3.4s
    """
    logger = get_logger()
    parts = [f"[{document_id}]", f"[{source}]", status]
    if message:
        parts.append(f"— {message}")
    for key, val in extras.items():
        parts.append(f"{key}={val}")
    logger.info(" ".join(parts))


def log_summary(total: int, scraped: int, skipped: int, failed: int, duration: float) -> None:
    """Log a run summary."""
    logger = get_logger()
    logger.info("=" * 70)
    logger.info("SCRAPER RUN COMPLETE")
    logger.info("  Total jobs:   %d", total)
    logger.info("  Scraped:      %d", scraped)
    logger.info("  Skipped:      %d", skipped)
    logger.info("  Failed:       %d", failed)
    logger.info("  Duration:     %.1fs", duration)
    logger.info("=" * 70)
