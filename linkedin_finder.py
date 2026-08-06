"""
LinkedIn Alumni & Staff Finder for RMIT Job Automation.

Generates targeted search queries and direct search links for RMIT students and staff
who currently or previously worked in a target job role.
"""

import logging
import re
import urllib.parse
from typing import List, Dict

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

logger = logging.getLogger(__name__)


def clean_job_title(title: str) -> str:
    """Clean job title for search queries."""
    title = re.sub(r"^(TEST ROLE:\s*|JOB:\s*)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\bJR\d+\b.*", "", title, flags=re.IGNORECASE)
    return title.strip()


def get_linkedin_search_url(job_title: str) -> str:
    """Generate a direct LinkedIn search URL for RMIT people in this role."""
    clean_title = clean_job_title(job_title)
    query = f'RMIT "{clean_title}"'
    encoded_query = urllib.parse.quote(query)
    return f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"


def find_linkedin_profiles(job_title: str, limit: int = 3) -> List[Dict]:
    """
    Search for RMIT students/staff on LinkedIn matching the job title.

    Returns:
        List of profile dicts with keys: name_title, link, snippet.
        If web search is blocked, returns fallback structured LinkedIn search target.
    """
    clean_title = clean_job_title(job_title)
    if not clean_title:
        return []

    search_query = f'site:linkedin.com/in "RMIT" "{clean_title}"'
    logger.info("Searching LinkedIn profiles for: %s", search_query)

    profiles = []

    if HAS_DDGS:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=limit * 3))
                for r in results:
                    url = r.get("href", "")
                    title = r.get("title", "")
                    snippet = r.get("body", "")

                    if "linkedin.com/in/" in url and ("RMIT" in title.upper() or "RMIT" in snippet.upper()):
                        clean_name = title.replace("- LinkedIn", "").replace("| LinkedIn", "").strip()
                        profiles.append({
                            "name_title": clean_name,
                            "link": url,
                            "snippet": snippet[:140] + "..." if len(snippet) > 140 else snippet,
                        })

                    if len(profiles) >= limit:
                        break
        except Exception as e:
            logger.warning("LinkedIn DDG search exception: %s", str(e))

    # If no specific profiles found via search API, return structured search link fallback
    if not profiles:
        direct_url = get_linkedin_search_url(clean_title)
        profiles.append({
            "name_title": f"Search RMIT People on LinkedIn in '{clean_title}'",
            "link": direct_url,
            "snippet": f"Click to find current RMIT students and alumni working as {clean_title} on LinkedIn.",
            "is_search_link": True
        })

    return profiles
