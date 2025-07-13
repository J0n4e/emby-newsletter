from source import configuration
from source import context
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from source.configuration import logging
from time import sleep


def send_email(html_content):
    try:
        smtp_server = smtplib.SMTP(configuration.conf.email.smtp_server, configuration.conf.email.smtp_port)
        smtp_server.connect(configuration.conf.email.smtp_server, configuration.conf.email.smtp_port)
        smtp_server.starttls()
        smtp_server.login(configuration.conf.email.smtp_user, configuration.conf.email.smtp_password)
    except Exception as e:
        raise Exception(f"Error while connecting to the SMTP server. Got error : {e}")

    for recipient in configuration.conf.recipients:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{configuration.conf.email_template.subject} for {context.placeholders['day_name']}"
        msg['From'] = configuration.conf.email.smtp_sender_email
        msg['To'] = recipient

        # Add both plain text and HTML parts
        text_part = MIMEText("Please view this email in an HTML-capable email client.", 'plain')
        html_part = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(text_part)
        msg.attach(html_part)

        smtp_server.sendmail(configuration.conf.email.smtp_sender_email, recipient, msg.as_string())
        logging.info(f"Email sent to {recipient}")
        sleep(2)
    smtp_server.quit()