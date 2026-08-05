"""
Workday CXS API client for fetching RMIT campus job listings.

Uses the undocumented but stable /wday/cxs/{tenant}/{site}/jobs endpoint
that powers Workday's candidate experience frontend.
"""

import logging
import time
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)


def fetch_job_listings(search_text: str = "", offset: int = 0) -> dict:
    """
    Fetch a page of job listings from the Workday CXS API.

    Args:
        search_text: Optional search query to filter jobs.
        offset: Pagination offset (0-indexed).

    Returns:
        Raw API response dict with keys: total, jobPostings, facets.

    Raises:
        requests.RequestException: On network or HTTP errors after retries.
    """
    payload = {
        "appliedFacets": {},
        "limit": config.WORKDAY_PAGE_SIZE,
        "offset": offset,
        "searchText": search_text,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    last_exception = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.post(
                config.WORKDAY_API_URL,
                json=payload,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(
                "Fetched page offset=%d, got %d postings (total=%d)",
                offset,
                len(data.get("jobPostings", [])),
                data.get("total", 0),
            )
            return data

        except requests.RequestException as e:
            last_exception = e
            if attempt < config.MAX_RETRIES:
                wait_time = config.RETRY_BACKOFF_FACTOR ** attempt
                logger.warning(
                    "Request failed (attempt %d/%d): %s. Retrying in %ds...",
                    attempt,
                    config.MAX_RETRIES,
                    str(e),
                    wait_time,
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    "Request failed after %d attempts: %s",
                    config.MAX_RETRIES,
                    str(e),
                )

    raise last_exception


def fetch_all_jobs(search_text: str = "") -> list[dict]:
    """
    Fetch ALL job listings, handling pagination automatically.

    Returns:
        List of job posting dicts from the API. Each contains:
        - title: Job title
        - externalPath: Unique job identifier / URL path
        - locationsText: Location string
        - postedOn: Posted date string
        - bulletFields: List of quick-info fields
    """
    all_jobs = []
    offset = 0

    first_page = fetch_job_listings(search_text=search_text, offset=0)
    total = first_page.get("total", 0)
    all_jobs.extend(first_page.get("jobPostings", []))

    logger.info("Total jobs available: %d", total)

    if total == 0:
        return all_jobs

    # Fetch remaining pages
    offset = config.WORKDAY_PAGE_SIZE
    while offset < total:
        time.sleep(1)  # Respectful rate limiting
        page = fetch_job_listings(search_text=search_text, offset=offset)
        postings = page.get("jobPostings", [])
        if not postings:
            break
        all_jobs.extend(postings)
        offset += config.WORKDAY_PAGE_SIZE

    logger.info("Fetched %d total job postings", len(all_jobs))
    return all_jobs


def fetch_job_detail(external_path: str) -> Optional[dict]:
    """
    Fetch the full detail of a single job posting.

    Args:
        external_path: The job's externalPath from the listings API
                       (e.g., "/job/Research-Assistant_JR12345").

    Returns:
        Full job detail dict including description, qualifications, etc.
        Returns None if the job is not found or request fails.
    """
    # external_path already starts with /job/...
    url = f"{config.WORKDAY_JOB_DETAIL_URL}{external_path}"

    headers = {
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        logger.debug("Fetched detail for: %s", external_path)
        return data
    except requests.RequestException as e:
        logger.warning("Failed to fetch job detail for %s: %s", external_path, str(e))
        return None
