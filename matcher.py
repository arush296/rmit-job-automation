"""
AI Resume Matcher for RMIT Job Automation.

Uses Google Gemini API to analyze a candidate's resume against a job description,
calculating fit score, matched/missing skills, key requirements, and targeted tips.
"""

import json
import logging
import os
import re
from typing import Optional

from google import genai
from google.genai import types

import config
import resume_parser

logger = logging.getLogger(__name__)


def get_gemini_client() -> Optional[genai.Client]:
    """Initialize and return the Google Gemini API client."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your-"):
        logger.warning("GEMINI_API_KEY not set or invalid in environment.")
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("Failed to initialize Gemini Client: %s", str(e))
        return None


def analyze_fit(
    job_title: str,
    job_description: str,
    resume_text: Optional[str] = None,
) -> Optional[dict]:
    """
    Analyze resume fit against a job description using Gemini AI.

    Args:
        job_title: Position title.
        job_description: Full HTML or text job description.
        resume_text: Optional explicit resume text. If None, auto-reads from resume/ folder.

    Returns:
        Dict with keys:
            - fit_percentage (int): 0-100 score
            - matched_skills (list[str]): Skills present in resume
            - missing_skills (list[str]): Skills needed by JD but missing/weak
            - fit_reasoning (str): Concise 1-2 sentence summary
            - key_requirements (list[str]): Top 3-4 JD requirements
            - application_tip (str): 1 actionable tip for applying
        Returns None if API key missing or analysis fails.
    """
    client = get_gemini_client()
    if not client:
        logger.warning("Skipping AI analysis (Gemini API key unavailable).")
        return None

    if not resume_text:
        resume_text = resume_parser.extract_resume_text()

    if not resume_text:
        logger.warning("Skipping AI analysis (no resume text extracted).")
        return None

    # Clean HTML tags from job description if present
    clean_jd = re.sub(r"<[^>]+>", " ", job_description)
    clean_jd = re.sub(r"\s+", " ", clean_jd).strip()

    prompt = f"""
You are an expert career advisor and technical recruiter for RMIT University.
Analyze the following candidate resume against the provided job posting for RMIT.

### JOB TITLE:
{job_title}

### JOB DESCRIPTION:
{clean_jd[:3000]}

### CANDIDATE RESUME:
{resume_text[:4000]}

---

Respond STRICTLY in raw JSON format with NO markdown wrapping, matching this exact schema:
{{
  "fit_percentage": <integer between 0 and 100>,
  "matched_skills": [<string list of top 3-5 matching skills found in resume>],
  "missing_skills": [<string list of 2-4 missing or weak skills required by JD>],
  "fit_reasoning": "<concise 1-2 sentence explanation of why the candidate is a good/moderate/weak fit>",
  "key_requirements": [<string list of top 3-4 core requirements extracted from JD>],
  "application_tip": "<1 actionable tip on how the candidate can highlight relevant projects or skills for this specific role>"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        response_text = response.text.strip()
        # Remove ```json wrapping if present
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        result = json.loads(response_text)
        logger.info(
            "AI Fit Analysis completed for '%s': %s%% match",
            job_title,
            result.get("fit_percentage", "N/A"),
        )
        return result

    except Exception as e:
        logger.error("Gemini API error during fit analysis for '%s': %s", job_title, str(e))
        return None
