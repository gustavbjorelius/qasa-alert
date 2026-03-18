# WHAT: Sends one email with links to new listings. Nothing else.
# CONTROL FLOW: main.py calls send_alert(new_listings) ->
#   builds a plain text email withone URL per line -> sends via Gmail SMTP.
# 
# GMAIL SETUP: (one time): 
#   myaccount.google.com -> Security -> App passwords -> create one -> copy it to SMTP_PASS
#   Use the 16-char App Password, NOT your real Gmail password.

import smtplib
import logging
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERT_EMAIL

logger = logging.getLogger(__name__)

def send_alert(new_listing):
    if not new_listing:
        return

    # One URL per line. That's the whole email.
    count = len(new_listing)
    lines = [f"{count} new match{'ar' if count > 1 else ''} on Qasa I Haninge:\n"]
    for listing in new_listings:
        lines.append(listing["url"])
        body = "\n".join(lines)

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"]  = f"Qasa: {count} new match in Haninge"
        msg["From"]     = SMTP_USER
        msg["To"]       = ALERT_EMAIL

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.startlts()   # encrypt before sending password 
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())
                logger.info("Alert sent: %d listings", count)
            except smtplib.SMTPAuthenticationError:
                logger.error("Auth failed - check SMTP_USER and SMTP_PASS")
            except smtplib.SMTPException as e:
                logger.error("SMTP error: %s, e)
