# RMIT Job Automation 

Automated monitoring of the [RMIT Jobs On Campus](https://rmit.wd3.myworkdayjobs.com/en-US/Job_On_Campus/jobs) portal. Get email notifications whenever new part-time/casual campus jobs are posted.

> [!NOTE]
> **Disclaimer:** This is an independent personal open-source project created strictly for personal job search automation. It is not affiliated with, endorsed by, sponsored by, or in any way officially connected with RMIT University or Workday, Inc.

## Features

- **Automatic polling** of RMIT's Workday job board via their JSON API
- **New job detection** using SQLite persistence across runs
- **Resume Analysis** powered by Google Gemini (fit percentage, matched skills, skills to highlight, application tips)
- **RMIT Networking Finder** with direct LinkedIn links to alumni & current staff in target roles
- **Branded email notifications** formatted in official RMIT colors (`#070759` Navy / `#E70129` Red)
- **GitHub Actions** scheduled workflow (every 2 hours, 100% free)
- `--dry-run` and `--test` modes for instant testing

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd rmitJobAutomation
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

**Required Credentials:**
- **Gmail App Password**: For sending notification emails ([Get App Password](https://myaccount.google.com/apppasswords))
- **Gemini API Key**: For AI resume analysis ([Get free key](https://aistudio.google.com/app/apikey))
- **Resume**: Place your PDF resume in `resume/resume.pdf` (gitignored to protect your privacy)

> [!WARNING]
> **Check your Spam / Junk folder!**
> Email providers (especially Gmail) may initially route automated notification emails to your Spam folder. 
> Make sure to open the first notification email and click **"Report not spam"** or add your sender address to your contacts so you don't miss future job alerts.

### 3. Test Locally

```bash
# Test Phase 2 pipeline locally (resume parsing, AI analysis & email preview)
python monitor.py --test --dry-run
```

### 4. Deploy to GitHub Actions

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add these repository secrets:
   - `SMTP_HOST` → `smtp.gmail.com`
   - `SMTP_PORT` → `587`
   - `SMTP_USER` → your Gmail address
   - `SMTP_PASSWORD` → your Gmail App Password
   - `NOTIFICATION_EMAIL` → recipient email address
   - `GEMINI_API_KEY` → your Gemini API Key
   - `RESUME_TEXT` → your extracted resume text (keeps your resume 100% private)
4. The workflow runs automatically every 2 hours, or trigger it manually from the **Actions** tab

## Project Structure

```
├── monitor.py          # Main orchestrator
├── scraper.py          # Workday API client
├── db.py               # SQLite persistence
├── resume_parser.py    # PDF/TXT resume reader & env fallback
├── matcher.py          # Gemini AI resume-to-JD fit analyzer
├── linkedin_finder.py  # RMIT student & alumni LinkedIn finder
├── notifier.py         # Email notification generator
├── config.py           # Configuration & constants
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
