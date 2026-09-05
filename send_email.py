"""
send_email.py
-------------
Gmail SMTP delivery using an app password. Free. No Azure email service.
"""
from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_digest(subject: str, html: str, text: str) -> None:
    sender = os.environ["GMAIL_FROM"]
    recipients = [addr.strip() for addr in os.environ["GMAIL_TO"].split(",") if addr.strip()]
    app_password = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")

    message = MIMEMultipart("alternative")
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(sender, app_password)
        smtp.sendmail(sender, recipients, message.as_string())
