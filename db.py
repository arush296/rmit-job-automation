"""
SQLite persistence layer for tracking seen job postings.

Stores jobs so we can diff against new API results and identify
newly posted jobs that haven't been notified about yet.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import config

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
    return conn


def init_db() -> None:
    """Create the jobs table if it doesn't exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                location TEXT,
                posted_date TEXT,
                url TEXT NOT NULL,
                bullet_fields TEXT,
                description TEXT,
                first_seen_at TEXT NOT NULL,
                notified INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        logger.debug("Database initialized at %s", config.DB_PATH)
    finally:
        conn.close()


def get_known_job_ids() -> set[str]:
    """Return the set of all job IDs we've already seen."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT id FROM jobs")
        return {row["id"] for row in cursor.fetchall()}
    finally:
        conn.close()


def insert_job(
    job_id: str,
    title: str,
    location: str,
    posted_date: str,
    url: str,
    bullet_fields: str = "",
    description: str = "",
) -> None:
    """Insert a new job into the database."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs (id, title, location, posted_date, url, 
                                        bullet_fields, description, first_seen_at, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                job_id,
                title,
                location,
                posted_date,
                url,
                bullet_fields,
                description,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        logger.debug("Inserted job: %s - %s", job_id, title)
    finally:
        conn.close()


def mark_notified(job_ids: list[str]) -> None:
    """Mark jobs as having been notified about."""
    if not job_ids:
        return

    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in job_ids)
        conn.execute(
            f"UPDATE jobs SET notified = 1 WHERE id IN ({placeholders})",
            job_ids,
        )
        conn.commit()
        logger.debug("Marked %d jobs as notified", len(job_ids))
    finally:
        conn.close()


def get_unnotified_jobs() -> list[dict]:
    """Return all jobs that haven't been notified about yet."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM jobs WHERE notified = 0 ORDER BY first_seen_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_job_count() -> int:
    """Return the total number of jobs in the database."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM jobs")
        return cursor.fetchone()["count"]
    finally:
        conn.close()


def get_job_by_id(job_id: str) -> Optional[dict]:
    """Fetch a single job by its ID."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
