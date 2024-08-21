import smtplib
import ssl

import certifi

from auditize.config import get_config


def send_email(to, subject, body):
    config = get_config()
    if not config.is_smtp_enabled():
        print("SMTP is disabled, print email information instead")
        print(to, subject, body)
        return

    message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context(cafile=certifi.where())
    with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
        server.starttls(context=context)
        server.login(config.smtp_username, config.smtp_password)
        server.sendmail(config.smtp_sender, to, message)
