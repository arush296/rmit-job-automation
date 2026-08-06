"""
Resume Parser Module for RMIT Job Automation.

Extracts text from PDF/TXT resumes located in the resume/ directory.
"""

import logging
import os
from typing import Optional
from pypdf import PdfReader

import config

logger = logging.getLogger(__name__)


def get_resume_path() -> Optional[str]:
    """Find the first PDF or TXT resume in the resume/ directory."""
    if not os.path.exists(config.RESUME_DIR):
        logger.warning("Resume directory does not exist: %s", config.RESUME_DIR)
        return None

    files = os.listdir(config.RESUME_DIR)
    for file in files:
        if file.startswith("."):
            continue
        ext = os.path.splitext(file)[1].lower()
        if ext in (".pdf", ".txt"):
            path = os.path.join(config.RESUME_DIR, file)
            logger.info("Found resume file: %s", path)
            return path

    logger.warning("No PDF or TXT resume found in %s", config.RESUME_DIR)
    return None


def extract_resume_text(file_path: Optional[str] = None) -> str:
    """
    Extract full text content from a resume file (PDF or TXT) or env variable RESUME_TEXT.

    Args:
        file_path: Optional specific path to resume. If None, auto-detects from resume/ folder.

    Returns:
        String containing extracted text, or empty string on failure.
    """
    # Check if RESUME_TEXT environment variable is set (ideal for secure GitHub Secrets)
    env_resume = os.getenv("RESUME_TEXT", "").strip()
    if env_resume:
        logger.info("Extracted %d characters from RESUME_TEXT environment variable", len(env_resume))
        return env_resume

    if file_path is None:
        file_path = get_resume_path()

    if not file_path or not os.path.exists(file_path):
        logger.error("Resume file path invalid or not found: %s", file_path)
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            logger.info("Extracted %d characters from TXT resume", len(text))
            return text.strip()

        elif ext == ".pdf":
            reader = PdfReader(file_path)
            pages_text = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages_text.append(page_text)
            full_text = "\n\n".join(pages_text).strip()
            logger.info(
                "Extracted %d characters across %d page(s) from PDF resume",
                len(full_text),
                len(reader.pages),
            )
            return full_text

        else:
            logger.error("Unsupported resume file format: %s", ext)
            return ""

    except Exception as e:
        logger.error("Error reading resume file %s: %s", file_path, str(e))
        return ""
