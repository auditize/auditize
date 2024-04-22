import smtplib
import ssl

import certifi

from .config import config


def send_email(to, subject, body):
    if not config.is_smtp_enabled():
        raise Exception("SMTP is not configured")

    message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context(cafile=certifi.where())
    with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
        server.starttls(context=context)
        server.login(config.smtp_username, config.smtp_password)
        server.sendmail(config.smtp_sender, to, message)
