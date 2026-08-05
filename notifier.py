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
<style>
  body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background-color: #f4f5f7; 
    margin: 0; 
    padding: 24px 12px; 
    color: #1a1a2e;
    -webkit-font-smoothing: antialiased;
  }
  .container { 
    max-width: 580px; 
    margin: 0 auto; 
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e1e4e8;
    box-shadow: 0 4px 16px rgba(0, 0, 84, 0.06);
  }
  .header { 
    background-color: #000054;
    border-bottom: 4px solid #E60028;
    color: #ffffff; 
    padding: 28px 32px;
  }
  .header-brand {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #E60028;
    margin-bottom: 6px;
  }
  .header h1 { 
    margin: 0; 
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: #ffffff;
  }
  .header p {
    margin: 6px 0 0; 
    color: rgba(255, 255, 255, 0.75); 
    font-size: 13.5px;
  }
  .content { 
    padding: 28px 32px;
  }
  .summary {
    background-color: #f8f9fa;
    border-left: 3px solid #000054;
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-size: 13.5px;
    line-height: 1.5;
    color: #4a5568;
  }
  .job-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 20px 22px;
    margin-bottom: 18px;
  }
  .job-title { 
    font-size: 17px; 
    font-weight: 600;
    line-height: 1.35;
    margin: 0 0 10px;
  }
  .job-title a { 
    color: #000054; 
    text-decoration: none;
  }
  .job-meta { 
    font-size: 12.5px; 
    color: #64748b;
    margin-bottom: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  .meta-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .meta-label {
    font-weight: 600;
    color: #475569;
  }
  .bullet-fields {
    margin-top: 12px;
    margin-bottom: 16px;
    line-height: 1.8;
  }
  .tag {
    display: inline-block;
    background: #f1f5f9;
    color: #1e293b;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    margin-right: 4px;
    margin-bottom: 4px;
    border: 1px solid #e2e8f0;
  }
  .apply-btn {
    display: inline-block;
    padding: 9px 20px;
    background: #E60028;
    color: #ffffff !important;
    text-decoration: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.2px;
  }
  .footer { 
    background-color: #fafafa;
    padding: 16px 32px;
    text-align: center;
    font-size: 11.5px;
    color: #94a3b8;
    border-top: 1px solid #f1f5f9;
  }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-brand">RMIT UNIVERSITY</div>
    <h1>New Campus Positions</h1>
    <p>{{ jobs|length }} new opportunity listed on Jobs On Campus</p>
  </div>
  <div class="content">
    <div class="summary">
      New employment opportunities have just been posted to the RMIT Jobs On Campus portal.
    </div>
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
      <a href="{{ job.url }}" class="apply-btn">View Job & Apply &rarr;</a>
    </div>
    {% endfor %}
  </div>
  <div class="footer">
    RMIT Job Automation &bull; System Check {{ check_time }}
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
