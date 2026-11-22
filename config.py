"""
Configuration for RMIT Job Automation.

Loads settings from environment variables (via .env file or GitHub Actions secrets).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Workday API ──────────────────────────────────────────────────────────────

WORKDAY_TENANT = "rmit"
WORKDAY_SITE = "Job_On_Campus"
WORKDAY_BASE_URL = f"https://{WORKDAY_TENANT}.wd3.myworkdayjobs.com"
WORKDAY_API_URL = f"{WORKDAY_BASE_URL}/wday/cxs/{WORKDAY_TENANT}/{WORKDAY_SITE}/jobs"
WORKDAY_JOB_DETAIL_URL = f"{WORKDAY_BASE_URL}/wday/cxs/{WORKDAY_TENANT}/{WORKDAY_SITE}"
WORKDAY_JOB_PAGE_URL = f"{WORKDAY_BASE_URL}/en-US/{WORKDAY_SITE}"

# API request settings
WORKDAY_PAGE_SIZE = 20  # Max jobs per API request
REQUEST_TIMEOUT = 30  # Seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 2s, 4s, 8s
RATE_LIMIT_BACKOFF_SECONDS = 30
MAX_RATE_LIMIT_WAIT_SECONDS = 300

# ─── Email / SMTP ────────────────────────────────────────────────────────────

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "jobs.db")
RESUME_DIR = os.path.join(BASE_DIR, "resume")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESUME_DIR, exist_ok=True)
