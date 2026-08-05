# RMIT Job Automation 

Automated monitoring of the [RMIT Jobs On Campus](https://rmit.wd3.myworkdayjobs.com/en-US/Job_On_Campus/jobs) portal. Get email notifications whenever new part-time/casual campus jobs are posted.

## Features

- **Automatic polling** of RMIT's Workday job board via their JSON API
- **New job detection** using SQLite persistence across runs
- **Email notifications** with a clean, branded HTML template
- **GitHub Actions** scheduled workflow (every 2 hours, free)
- `--dry-run` mode for testing without sending emails

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd rmitJobAutomation
pip install -r requirements.txt
```

### 2. Configure Email

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

**Gmail Setup:**
1. Enable [2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification) on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords) (select "Mail")
3. Use the 16-character app password as `SMTP_PASSWORD` in `.env`

### 3. Test Locally

```bash
# Dry run — checks API, detects new jobs, saves email preview (no email sent)
python monitor.py --dry-run

# With debug output
python monitor.py --dry-run --debug
```

### 4. Deploy to GitHub Actions

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add these repository secrets:
   - `SMTP_HOST` → `smtp.gmail.com`
   - `SMTP_PORT` → `587`
   - `SMTP_USER` → your Gmail address
   - `SMTP_PASSWORD` → your Gmail App Password
   - `NOTIFICATION_EMAIL` → where to receive notifications
4. The workflow runs automatically every 2 hours, or trigger it manually from the **Actions** tab

## Project Structure

```
├── monitor.py          # Main entry point
├── scraper.py          # Workday API client
├── db.py               # SQLite persistence
├── notifier.py         # Email notifications
├── config.py           # Configuration
├── .env.example        # Environment template
├── requirements.txt    # Python dependencies
└── .github/workflows/
    └── monitor.yml     # GitHub Actions cron workflow
```

## How It Works

1. **Poll** — Calls Workday's internal CXS API to get current job listings
2. **Diff** — Compares against previously seen jobs stored in SQLite
3. **Fetch** — Gets full job descriptions for any new postings
4. **Notify** — Sends a styled HTML email with job details and apply links
5. **Track** — Stores new jobs and marks them as notified

## Phase 2 (Coming Soon)

- AI-powered resume-to-JD matching using Google Gemini
- Fit percentage scoring and skill gap analysis
- Tailored application suggestions in notifications
