"""
Main orchestrator for the RMIT Job Monitor.

Ties together: scraper → DB diff → notifier.
Run with: python monitor.py [--dry-run]
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone

import config
import db
import linkedin_finder
import matcher
import notifier
import scraper

# ─── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("monitor")


def process_job_posting(job_data: dict) -> dict:
    """
    Transform a raw Workday API job posting into our internal format.

    Args:
        job_data: Raw job dict from the Workday CXS API.

    Returns:
        Cleaned job dict ready for DB insertion and notification.
    """
    external_path = job_data.get("externalPath", "")
    title = job_data.get("title", "Unknown Position")
    locations = job_data.get("locationsText", "")
    posted_on = job_data.get("postedOn", "")
    bullet_fields = job_data.get("bulletFields", [])

    # Build the direct application URL
    url = f"{config.WORKDAY_JOB_PAGE_URL}{external_path}"

    # Join bullet fields with pipe separator for storage
    bullets_str = " | ".join(bullet_fields) if bullet_fields else ""

    return {
        "id": external_path,
        "title": title,
        "location": locations,
        "posted_date": posted_on,
        "url": url,
        "bullet_fields": bullets_str,
    }


def fetch_job_description(external_path: str) -> str:
    """
    Fetch the full job description for a posting.

    Args:
        external_path: The job's externalPath.

    Returns:
        Job description HTML string, or empty string on failure.
    """
    detail = scraper.fetch_job_detail(external_path)
    if not detail:
        return ""

    # The description is typically in jobPostingInfo.jobDescription
    job_info = detail.get("jobPostingInfo", {})
    return job_info.get("jobDescription", "")


def run_monitor(dry_run: bool = False) -> None:
    """Discover new jobs and send alerts for jobs awaiting notification."""
    check_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    logger.info("=" * 60)
    logger.info("RMIT Job Monitor — Starting check at %s", check_time)
    logger.info("=" * 60)

    # Step 1: Initialize database
    db.init_db()
    known_ids = db.get_known_job_ids()
    logger.info("Known jobs in DB: %d", len(known_ids))

    # Step 2: Fetch current listings from Workday
    logger.info("Fetching jobs from Workday API...")
    fetch_failed = False
    try:
        raw_jobs = scraper.fetch_all_jobs()
    except Exception as e:
        logger.error("Failed to fetch jobs: %s", str(e))
        raw_jobs = []
        fetch_failed = True
    else:
        logger.info("Jobs returned by API: %d", len(raw_jobs))

    new_jobs = {}
    for raw_job in raw_jobs:
        job = process_job_posting(raw_job)
        if job["id"] not in known_ids:
            new_jobs[job["id"]] = job

    pending_jobs = db.get_unnotified_jobs()
    jobs_to_notify = list(new_jobs.values()) + pending_jobs
    logger.info("New jobs found: %d. Pending alerts: %d", len(new_jobs), len(pending_jobs))

    if not jobs_to_notify:
        if fetch_failed:
            sys.exit(1)
        logger.info("No job alerts to send.")
        return

    for job in jobs_to_notify:
        logger.info("  → Processing: %s (%s)", job["title"], job["location"])
        if job["id"] in new_jobs:
            job["description"] = fetch_job_description(job["id"])
            if not dry_run:
                db.insert_job(
                    job_id=job["id"],
                    title=job["title"],
                    location=job["location"],
                    posted_date=job["posted_date"],
                    url=job["url"],
                    bullet_fields=job["bullet_fields"],
                    description=job["description"],
                )

        job["fit_analysis"] = matcher.analyze_fit(
            job_title=job["title"],
            job_description=job["description"] or job["bullet_fields"] or "",
        )

        job["linkedin_profiles"] = linkedin_finder.find_linkedin_profiles(
            job_title=job["title"],
            limit=3,
        )

        time.sleep(0.5)  # Rate limiting

    logger.info("Sending notification for %d job(s)...", len(jobs_to_notify))
    success = notifier.notify_new_jobs(
        jobs=jobs_to_notify, dry_run=dry_run, check_time=check_time
    )

    if not success:
        logger.error("❌ Failed to send notification.")
        sys.exit(1)

    if dry_run:
        logger.info("Notification preview generated.")
    else:
        db.mark_notified([job["id"] for job in jobs_to_notify])
        logger.info("✅ Notification sent successfully!")

    if fetch_failed:
        sys.exit(1)

    # Summary
    total_in_db = db.get_job_count()
    logger.info("─" * 40)
    logger.info("Summary: %d new, %d total tracked", len(new_jobs), total_in_db)
    logger.info("Monitor check complete.")


def main():
    parser = argparse.ArgumentParser(
        description="RMIT Jobs On Campus Monitor",
        epilog="Checks for new job postings and sends email notifications.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending emails (prints to console and saves HTML preview)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Inject a test job to verify email sending and notification styling",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug-level logging",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test:
        logger.info("🧪 Running in TEST mode (injecting a mock job posting with Phase 2 AI matching)")
        db.init_db()
        test_title = "TEST ROLE: Peer Learning Advisor / Student Assistant"
        test_jd = "Assisting RMIT students with academic learning, peer support, software project guidance, teamwork, and program administration."
        
        fit_analysis = matcher.analyze_fit(
            job_title=test_title,
            job_description=test_jd,
        )

        linkedin_profiles = linkedin_finder.find_linkedin_profiles(
            job_title="Peer Learning Advisor",
            limit=3,
        )

        test_job = [{
            "id": f"/job/test-position-{int(time.time())}",
            "title": test_title,
            "location": "City Campus (Melbourne)",
            "posted_date": "Posted Just Now",
            "url": f"{config.WORKDAY_JOB_PAGE_URL}/jobs",
            "bullet_fields": "Casual | $38.50/hr | Flexible Hours | On Campus",
            "description": test_jd,
            "fit_analysis": fit_analysis,
            "linkedin_profiles": linkedin_profiles,
        }]
        check_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        success = notifier.notify_new_jobs(jobs=test_job, dry_run=args.dry_run, check_time=check_time)
        if success:
            logger.info("✅ Test email sent successfully! Check your inbox.")
        else:
            logger.error("❌ Failed to send test email. Check your SMTP secrets.")
            sys.exit(1)
        return

    if args.dry_run:
        logger.info("🔍 Running in DRY RUN mode (no emails will be sent)")

    run_monitor(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
