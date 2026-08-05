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
<html>
<head>
<style>
  body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f5f5f5; 
    margin: 0; 
    padding: 20px; 
    color: #333;
  }
  .container { 
    max-width: 600px; 
    margin: 0 auto; 
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  .header { 
    background: linear-gradient(135deg, #000054, #E60028);
    color: white; 
    padding: 24px 30px;
  }
  .header h1 { 
    margin: 0; 
    font-size: 22px;
    font-weight: 600;
  }
  .header p {
    margin: 8px 0 0; 
    opacity: 0.85; 
    font-size: 14px;
  }
  .content { 
    padding: 24px 30px;
  }
  .job-card {
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
  }
  .job-card:hover {
    border-color: #000054;
  }
  .job-title { 
    font-size: 18px; 
    font-weight: 600;
    color: #000054;
    margin: 0 0 8px;
  }
  .job-title a { 
    color: #000054; 
    text-decoration: none;
  }
  .job-title a:hover { 
    text-decoration: underline;
  }
  .job-meta { 
    font-size: 13px; 
    color: #666;
    margin-bottom: 12px;
  }
  .job-meta span {
    margin-right: 16px;
  }
  .bullet-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
  }
  .tag {
    background: #f0f0ff;
    color: #000054;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }
  .apply-btn {
    display: inline-block;
    margin-top: 14px;
    padding: 10px 24px;
    background: #E60028;
    color: white !important;
    text-decoration: none;
    border-radius: 25px;
    font-size: 14px;
    font-weight: 600;
  }
  .footer { 
    padding: 16px 30px;
    text-align: center;
    font-size: 12px;
    color: #999;
    border-top: 1px solid #f0f0f0;
  }
  .summary {
    background: #f8f8ff;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    font-size: 14px;
    color: #444;
  }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🎓 New RMIT Campus Jobs</h1>
    <p>{{ jobs|length }} new position{{ 's' if jobs|length > 1 else '' }} found on Jobs On Campus</p>
  </div>
  <div class="content">
    <div class="summary">
      These jobs were just posted to the RMIT Jobs On Campus portal. 
      Apply early for the best chance!
    </div>
    {% for job in jobs %}
    <div class="job-card">
      <h2 class="job-title">
        <a href="{{ job.url }}">{{ job.title }}</a>
      </h2>
      <div class="job-meta">
        {% if job.location %}<span>📍 {{ job.location }}</span>{% endif %}
        {% if job.posted_date %}<span>📅 {{ job.posted_date }}</span>{% endif %}
      </div>
      {% if job.bullet_fields %}
      <div class="bullet-fields">
        {% for field in job.bullet_fields.split('|') if field.strip() %}
        <span class="tag">{{ field.strip() }}</span>
        {% endfor %}
      </div>
      {% endif %}
      <a href="{{ job.url }}" class="apply-btn">View & Apply →</a>
    </div>
    {% endfor %}
  </div>
  <div class="footer">
    RMIT Job Automation • Checked at {{ check_time }}
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
