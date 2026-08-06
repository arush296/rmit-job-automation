"""
Email notification sender for new RMIT job postings.

Sends HTML-formatted emails via Gmail SMTP with App Password authentication.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template

import config

logger = logging.getLogger(__name__)

# ─── Email HTML Template ─────────────────────────────────────────────────────

EMAIL_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<style>
  :root {
    color-scheme: light;
  }
  body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background-color: #f4f5f7; 
    margin: 0; 
    padding: 24px 12px; 
    color: #1a1a2e;
    -webkit-font-smoothing: antialiased;
  }
  .container { 
    max-width: 560px; 
    margin: 0 auto; 
    background: #ffffff;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e1e4e8;
  }
  .header { 
    background-color: #070759 !important;
    border-bottom: 4px solid #E70129 !important;
    color: #ffffff !important; 
    padding: 24px 28px;
  }
  .header-brand {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #E70129 !important;
    margin-bottom: 4px;
  }
  .header h1 { 
    margin: 0; 
    font-size: 20px;
    font-weight: 700;
    color: #ffffff !important;
  }
  .content { 
    padding: 24px 28px;
  }
  .job-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 14px;
  }
  .job-card:last-child {
    margin-bottom: 0;
  }
  .job-title { 
    font-size: 16px; 
    font-weight: 700;
    line-height: 1.4;
    margin: 0 0 10px;
  }
  .job-title a { 
    color: #070759; 
    text-decoration: none;
  }
  .job-meta { 
    font-size: 13px; 
    color: #475569;
    margin-bottom: 12px;
  }
  .meta-item {
    display: inline-block;
    margin-right: 16px;
  }
  .meta-label {
    font-weight: 600;
    color: #070759;
  }
  .bullet-fields {
    margin-top: 10px;
    margin-bottom: 14px;
  }
  .tag {
    display: inline-block;
    background: #f1f5f9;
    color: #070759;
    padding: 3px 9px;
    border-radius: 4px;
    font-size: 11.5px;
    font-weight: 500;
    margin-right: 4px;
    margin-bottom: 4px;
    border: 1px solid #e2e8f0;
  }
  
  /* ─── Phase 2 AI Match Styles ────────────────────────────────────────── */
  .match-box {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 14px 16px;
    margin-top: 14px;
    margin-bottom: 14px;
  }
  .match-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  .score-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 13px;
    color: #ffffff !important;
  }
  .score-high { background-color: #16a34a !important; }
  .score-mid { background-color: #d97706 !important; }
  .score-low { background-color: #dc2626 !important; }
  
  .match-section-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #070759;
    margin-top: 10px;
    margin-bottom: 4px;
  }
  .match-text {
    font-size: 12.5px;
    color: #334155;
    line-height: 1.45;
    margin: 0;
  }
  .skill-tag-matched {
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #bbf7d0;
  }
  .skill-tag-missing {
    background: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fecaca;
  }
  .linkedin-section {
    background-color: #f0f4f8;
    border-left: 3px solid #0077b5;
    padding: 10px 14px;
    border-radius: 0 4px 4px 0;
    margin-top: 12px;
  }
  .linkedin-title {
    font-size: 12px;
    font-weight: 700;
    color: #0077b5;
    margin-bottom: 4px;
  }
  .linkedin-link {
    font-size: 12px;
    color: #0077b5;
    text-decoration: none;
  }
  .linkedin-link:hover {
    text-decoration: underline;
  }

  .apply-btn {
    display: inline-block;
    padding: 8px 18px;
    background: #E70129 !important;
    color: #ffffff !important;
    text-decoration: none;
    border-radius: 5px;
    font-size: 12.5px;
    font-weight: 600;
    margin-top: 6px;
  }
  .footer { 
    background-color: #fafafa;
    padding: 16px 28px;
    text-align: center;
    font-size: 11px;
    color: #94a3b8;
    border-top: 1px solid #f1f5f9;
  }
  .disclaimer {
    font-size: 10px;
    color: #a0aec0;
    margin-top: 6px;
    display: block;
    line-height: 1.4;
  }
</style>
</head>
<body>
<div class="container">
  <div class="header" style="background-color: #070759 !important;">
    <div class="header-brand" style="color: #E70129 !important;">RMIT JOBS ON CAMPUS</div>
    <h1 style="color: #ffffff !important;">{{ jobs|length }} New Position{{ 's' if jobs|length > 1 else '' }} Posted</h1>
  </div>
  <div class="content">
    {% for job in jobs %}
    <div class="job-card">
      <h2 class="job-title">
        <a href="{{ job.url }}">{{ job.title }}</a>
      </h2>
      <div class="job-meta">
        {% if job.location %}
        <span class="meta-item"><span class="meta-label">Location:</span> {{ job.location }}</span>
        {% endif %}
        {% if job.posted_date %}
        <span class="meta-item"><span class="meta-label">Posted:</span> {{ job.posted_date }}</span>
        {% endif %}
      </div>
      {% if job.bullet_fields %}
      <div class="bullet-fields">
        {% for field in job.bullet_fields.split('|') if field.strip() %}
        <span class="tag">{{ field.strip() }}</span>
        {% endfor %}
      </div>
      {% endif %}

      {% if job.fit_analysis %}
      <div class="match-box">
        <div class="match-header">
          <span class="match-section-title" style="margin: 0;">AI Resume Match Analysis</span>
          <span class="score-badge {% if job.fit_analysis.fit_percentage >= 75 %}score-high{% elif job.fit_analysis.fit_percentage >= 50 %}score-mid{% else %}score-low{% endif %}">
            {{ job.fit_analysis.fit_percentage }}% Match
          </span>
        </div>
        
        {% if job.fit_analysis.fit_reasoning %}
        <p class="match-text" style="margin-bottom: 8px;">{{ job.fit_analysis.fit_reasoning }}</p>
        {% endif %}

        {% if job.fit_analysis.matched_skills %}
        <div class="match-section-title">Matched Skills</div>
        <div>
          {% for skill in job.fit_analysis.matched_skills %}
          <span class="tag skill-tag-matched">{{ skill }}</span>
          {% endfor %}
        </div>
        {% endif %}

        {% if job.fit_analysis.missing_skills %}
        <div class="match-section-title">Skills to Highlight / Bridge</div>
        <div>
          {% for skill in job.fit_analysis.missing_skills %}
          <span class="tag skill-tag-missing">{{ skill }}</span>
          {% endfor %}
        </div>
        {% endif %}

        {% if job.fit_analysis.application_tip %}
        <div class="match-section-title">Application Tip</div>
        <p class="match-text"><em>{{ job.fit_analysis.application_tip }}</em></p>
        {% endif %}
      </div>
      {% endif %}

      {% if job.linkedin_profiles %}
      <div class="linkedin-section">
        <div class="linkedin-title">RMIT Network & Alumni in this Role:</div>
        {% for profile in job.linkedin_profiles %}
        <div style="margin-bottom: 4px;">
          <a href="{{ profile.link }}" class="linkedin-link" target="_blank">&rarr; {{ profile.name_title }}</a>
        </div>
        {% endfor %}
      </div>
      {% endif %}

      <div style="margin-top: 14px;">
        <a href="{{ job.url }}" class="apply-btn" style="background-color: #E70129 !important; color: #ffffff !important;">View Job & Apply &rarr;</a>
      </div>
    </div>
    {% endfor %}
  </div>
  <div class="footer">
    RMIT Job Automation &bull; System Check {{ check_time }}
    <span class="disclaimer">
      Independent personal project. Not affiliated with, endorsed by, or associated with RMIT University or Workday.
    </span>
  </div>
</div>
</body>
</html>
""")


def send_email(subject: str, html_body: str, dry_run: bool = False) -> bool:
    """
    Send an HTML email via SMTP.

    Args:
        subject: Email subject line.
        html_body: HTML content of the email.
        dry_run: If True, log instead of sending.

    Returns:
        True if sent (or dry_run), False on failure.
    """
    if dry_run:
        logger.info("[DRY RUN] Would send email:")
        logger.info("  To: %s", config.NOTIFICATION_EMAIL)
        logger.info("  Subject: %s", subject)
        logger.info("  Body length: %d chars", len(html_body))
        return True

    if not all([config.SMTP_USER, config.SMTP_PASSWORD, config.NOTIFICATION_EMAIL]):
        logger.error(
            "Email not configured. Set SMTP_USER, SMTP_PASSWORD, and "
            "NOTIFICATION_EMAIL in .env"
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = config.SMTP_USER
    msg["To"] = config.NOTIFICATION_EMAIL
    msg["Subject"] = subject

    # Plain text fallback
    plain_text = f"{subject}\n\nView jobs at: {config.WORKDAY_JOB_PAGE_URL}/jobs"
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent successfully to %s", config.NOTIFICATION_EMAIL)
        return True

    except smtplib.SMTPException as e:
        logger.error("Failed to send email: %s", str(e))
        return False


def notify_new_jobs(
    jobs: list[dict], dry_run: bool = False, check_time: str = ""
) -> bool:
    """
    Send a notification email about new job postings.

    Args:
        jobs: List of job dicts (from db.py or processed scraper output).
        dry_run: If True, log instead of sending.
        check_time: Timestamp string for the email footer.

    Returns:
        True if notification sent successfully.
    """
    if not jobs:
        logger.info("No new jobs to notify about.")
        return True

    count = len(jobs)
    subject = f"🎓 {count} New RMIT Campus Job{'s' if count > 1 else ''} Posted!"

    html_body = EMAIL_TEMPLATE.render(jobs=jobs, check_time=check_time)

    if dry_run:
        # Also save the HTML for preview
        import os
        preview_path = os.path.join(config.DATA_DIR, "email_preview.html")
        with open(preview_path, "w") as f:
            f.write(html_body)
        logger.info("[DRY RUN] Email preview saved to: %s", preview_path)

    return send_email(subject, html_body, dry_run=dry_run)
