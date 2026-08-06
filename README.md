# RMIT Job Automation 🎓

Automated monitoring of the [RMIT Jobs On Campus](https://rmit.wd3.myworkdayjobs.com/en-US/Job_On_Campus/jobs) portal. Get email notifications whenever new part-time/casual campus jobs are posted, complete with **AI Resume Analysis** and **LinkedIn RMIT Networking links**.

> [!NOTE]
> **Disclaimer:** This is an independent personal open-source project created strictly for personal job search automation. It is not affiliated with, endorsed by, sponsored by, or in any way officially connected with RMIT University or Workday, Inc.

---

## Features

- **Automatic Polling**: Fetches RMIT's Workday job board via their JSON API
- **New Job Detection**: Uses SQLite persistence (`jobs.db`) to ensure no duplicate notifications
- **AI Resume Analysis**: Evaluates job descriptions against your resume using Google Gemini 2.5 Flash:
  - **Fit Percentage Score** (e.g. `92% Match`)
  - **Matched Skills** (skills found in your resume)
  - **Skills to Highlight / Bridge** (skills required by JD)
  - **Actionable Application Tip**
- **RMIT Networking Finder**: Locates current RMIT students and alumni on LinkedIn in target roles
- **Branded HTML Emails**: Designed in official RMIT colors (`#070759` Navy / `#E70129` Red)
- **GitHub Actions**: 24/7 automated scheduled workflow (runs every 2 hours, 100% free)
- **Privacy First**: Your resume is kept 100% private using GitHub Secrets (never committed to git)

---

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd rmitJobAutomation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Local Configuration (`.env`):**
- `SMTP_USER` & `SMTP_PASSWORD`: Your Gmail address and [Gmail App Password](https://myaccount.google.com/apppasswords)
- `NOTIFICATION_EMAIL`: Where you want to receive alerts
- `GEMINI_API_KEY`: Your Google Gemini API Key ([Get free key](https://aistudio.google.com/app/apikey))
- **Local Resume**: Place your PDF resume inside the `resume/` folder (e.g. `resume/my_resume.pdf`). Note: `resume/` is gitignored to protect your privacy.

> [!WARNING]
> **Check your Spam / Junk folder!**
> Email providers (especially Gmail) may initially route automated notification emails to your Spam folder. 
> Make sure to open the first notification email and click **"Report not spam"** or add your sender address to your contacts so you don't miss future job alerts.

---

## Secure Setup for GitHub Actions (Private Resume)

To keep your resume completely private while enabling AI Resume Analysis on GitHub Actions:

### Step A: Extract your Resume Text
Run this command in your terminal to extract your resume text and copy it directly to your Mac clipboard:

```bash
source .venv/bin/activate && python3 -c "import resume_parser; print(resume_parser.extract_resume_text())" | pbcopy
```

*(On Windows / Linux, omit `| pbcopy` and copy the printed text manually).*

### Step B: Add Repository Secrets
1. Go to your GitHub repository on GitHub.
2. Navigate to **Settings → Secrets and variables → Actions**.
3. Click **New repository secret** and add the following:

| Secret Name | Value / Description |
| :--- | :--- |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Your 16-character [Gmail App Password](https://myaccount.google.com/apppasswords) |
| `NOTIFICATION_EMAIL` | Email address where alerts should be sent |
| `GEMINI_API_KEY` | Your [Google Gemini API Key](https://aistudio.google.com/app/apikey) |
| `RESUME_TEXT` | Paste the extracted resume text copied from Step A |

---

## Testing

### Test Locally (Dry Run)
Generate a test job with AI Resume Analysis and preview the HTML email locally without sending an email:

```bash
python monitor.py --test --dry-run
```
*(Saved preview will be at `data/email_preview.html`).*

### Test on GitHub Actions
1. Go to your repo's **Actions** tab on GitHub.
2. Select **RMIT Job Monitor** ➔ **Run workflow**.
3. Check **"Send a test email with a mock job posting"** and click **Run workflow**.

---

## How It Works

```
Workday API ➔ scraper.py ➔ SQLite Diff (db.py) ➔ Gemini AI Matcher (matcher.py)
                                                      ↓
                                           LinkedIn Finder (linkedin_finder.py)
                                                      ↓
                                            Email Notifier (notifier.py)
```

1. **Poll** — Calls Workday's internal CXS API (`/wday/cxs/rmit/Job_On_Campus/jobs`) for listings.
2. **Diff** — Compares against previously seen jobs in SQLite `jobs.db`.
3. **Fetch & Analyze** — Fetches full job descriptions, extracts resume text from `RESUME_TEXT` secret, and runs Gemini 2.5 Flash AI analysis.
4. **LinkedIn Search** — Searches public LinkedIn profiles for RMIT alumni/staff in that role.
5. **Notify** — Sends an HTML email formatted with match percentage, skill breakdown, application tips, and networking links.

---

## Project Structure

```
rmitJobAutomation/
├── monitor.py          # Main orchestrator
├── scraper.py          # Workday CXS API client
├── db.py               # SQLite persistence layer
├── resume_parser.py    # Resume text extractor (PDF/TXT & RESUME_TEXT env fallback)
├── matcher.py          # Gemini AI resume-to-JD fit analyzer
├── linkedin_finder.py  # RMIT student & alumni LinkedIn search finder
├── notifier.py         # Branded HTML email notification generator
├── config.py           # Configuration & constants
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── .github/
    └── workflows/
        └── monitor.yml # GitHub Actions 2-hour cron workflow
```
