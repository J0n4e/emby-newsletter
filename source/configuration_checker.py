from source.configuration import conf
from source.configuration import logging
import re
from urllib.parse import urlparse


def check_server_configuration():
    # Server URL
    parsed_url = urlparse(conf.server.url)
    assert parsed_url.scheme != '', f"[FATAL] Invalid Server URL. The URL must contain the scheme (e.g. http:// or https://). Please check the configuration. Got {conf.server.url}. Parsed : {parsed_url}"
    assert parsed_url.netloc != '', f"[FATAL] Invalid Server URL. The URL must contain a valid host (e.g. example.com or 127.0.0.1:80). Please check the configuration. Got {conf.server.url}. Parsed : {parsed_url}"

    # Server API token
    assert isinstance(conf.server.api_token,
                      str), "[FATAL] Invalid Server API token. The API token must be a string. Please check the configuration."
    assert conf.server.api_token != '', "[FATAL] Invalid Server API token. The API token cannot be empty. Please check the configuration."

    # watched_film_folders
    assert isinstance(conf.server.watched_film_folders,
                      list), "[FATAL] Invalid watched film folders. The watched film folders must be a list. Please check the configuration."

    # watched_tv_folders
    assert isinstance(conf.server.watched_tv_folders,
                      list), "[FATAL] Invalid watched TV folders. The watched TV folders must be a list. Please check the configuration."

    # observed_period_days
    assert isinstance(conf.server.observed_period_days,
                      int), "[FATAL] Invalid observed period days. The observed period days must be an integer. Please check the configuration."


def check_tmdb_configuration():
    # TMDB API key
    assert isinstance(conf.tmdb.api_key,
                      str), "[FATAL] Invalid TMDB API key. The API key must be a string. Please check the configuration."
    assert conf.tmdb.api_key != '', "[FATAL] Invalid TMDB API key. The API key cannot be empty. Please check the configuration."


def email_template_configuration():
    # Language
    assert isinstance(conf.email_template.language,
                      str), "[FATAL] Invalid email template language. The language must be a string. Please check the configuration."
    assert conf.email_template.language in ['en',
                                            'fr'], "[FATAL] Invalid email template language. The language must be either 'en' or 'fr'. Please check the configuration."

    # Subject
    assert isinstance(conf.email_template.subject,
                      str), "[FATAL] Invalid email template subject. The subject must be a string. Please check the configuration."

    # Title
    assert isinstance(conf.email_template.title,
                      str), "[FATAL] Invalid email template title. The title must be a string. Please check the configuration."

    # Subtitle
    assert isinstance(conf.email_template.subtitle,
                      str), "[FATAL] Invalid email template subtitle. The subtitle must be a string. Please check the configuration."

    # Server URL
    assert isinstance(conf.email_template.server_url,
                      str), "[FATAL] Invalid email template Server URL. The Server URL must be a string. Please check the configuration."

    # Unsubscribe email
    assert isinstance(conf.email_template.unsubscribe_email,
                      str), "[FATAL] Invalid email template unsubscribe email. The unsubscribe email must be a string. Please check the configuration."

    # Server owner name
    assert isinstance(conf.email_template.server_owner_name,
                      str), "[FATAL] Invalid email template Server owner name. The Server owner name must be a string. Please check the configuration."


def check_email_configuration():
    # SMTP server
    assert isinstance(conf.email.smtp_server,
                      str), "[FATAL] Invalid email SMTP server. The SMTP server must be a string. Please check the configuration."
    assert conf.email.smtp_server != '', "[FATAL] Invalid email SMTP server. The SMTP server cannot be empty. Please check the configuration."

    # SMTP port
    assert isinstance(conf.email.smtp_port,
                      int), "[FATAL] Invalid email SMTP port. The SMTP port must be an integer. Please check the configuration."
    assert conf.email.smtp_port > 0, "[FATAL] Invalid email SMTP port. The SMTP port must be greater than 0. Please check the configuration."

    # SMTP username
    assert isinstance(conf.email.smtp_user,
                      str), "[FATAL] Invalid email SMTP username. The SMTP username must be a string. Please check the configuration."
    assert conf.email.smtp_user != '', "[FATAL] Invalid email SMTP username. The SMTP username cannot be empty. Please check the configuration."

    # SMTP password
    assert isinstance(conf.email.smtp_password,
                      str), "[FATAL] Invalid email SMTP password. The SMTP password must be a string. Please check the configuration."
    assert conf.email.smtp_password != '', "[FATAL] Invalid email SMTP password. The SMTP password cannot be empty. Please check the configuration."


def check_recipients_configuration():
    # Recipients
    assert isinstance(conf.recipients,
                      list), "[FATAL] Invalid recipients configuration. The recipients must be a list. Please check the configuration."


def check_scheduler_configuration():
    if conf.scheduler.enabled:
        assert isinstance(conf.scheduler.cron,
                          str), "[FATAL] Invalid scheduler cron expression. The cron expression must be a string. Please check the configuration."


def check_configuration():
    """
    Check if the configuration is valid.
    The goal is to ensure all  values fetched from the configuration file are valid.
    """
    check_server_configuration()
    check_tmdb_configuration()
    email_template_configuration()
    check_email_configuration()
    check_recipients_configuration()