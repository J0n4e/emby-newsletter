#!/usr/bin/env python3
"""
Configuration management for Emby Newsletter
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EmbyConfig:
    """Emby server configuration"""
    url: str
    api_token: str
    watched_film_folders: List[str] = field(default_factory=list)
    watched_tv_folders: List[str] = field(default_factory=list)
    observed_period_days: int = 30


@dataclass
class TMDBConfig:
    """TMDB API configuration"""
    api_key: str


@dataclass
class EmailTemplateConfig:
    """Email template configuration"""
    language: str = "en"
    subject: str = ""
    title: str = ""
    subtitle: str = ""
    emby_url: str = ""
    unsubscribe_email: str = ""
    emby_owner_name: str = ""


@dataclass
class EmailConfig:
    """SMTP email configuration"""
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender_email: str


@dataclass
class SchedulerConfig:
    """Scheduler configuration"""
    cron: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration"""
    emby: EmbyConfig
    tmdb: TMDBConfig
    email_template: EmailTemplateConfig
    email: EmailConfig
    recipients: List[str] = field(default_factory=list)
    scheduler: Optional[SchedulerConfig] = None


class ConfigurationManager:
    """Manages application configuration"""

    def __init__(self, config_path: str = "/app/config/config.yml"):
        self.config_path = config_path
        self._config: Optional[AppConfig] = None

    def load_config(self) -> AppConfig:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as file:
                raw_config = yaml.safe_load(file)

            self._config = self._parse_config(raw_config)
            self._validate_config(self._config)

            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self._config

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def _parse_config(self, raw_config: Dict[str, Any]) -> AppConfig:
        """Parse raw configuration dictionary into typed configuration objects"""
        try:
            # Parse Emby configuration
            emby_config = EmbyConfig(
                url=raw_config['emby']['url'].rstrip('/'),
                api_token=raw_config['emby']['api_token'],
                watched_film_folders=raw_config['emby'].get('watched_film_folders', []),
                watched_tv_folders=raw_config['emby'].get('watched_tv_folders', []),
                observed_period_days=raw_config['emby'].get('observed_period_days', 30)
            )

            # Parse TMDB configuration
            tmdb_config = TMDBConfig(
                api_key=raw_config['tmdb']['api_key']
            )

            # Parse email template configuration
            email_template_config = EmailTemplateConfig(
                language=raw_config['email_template'].get('language', 'en'),
                subject=raw_config['email_template'].get('subject', ''),
                title=raw_config['email_template'].get('title', ''),
                subtitle=raw_config['email_template'].get('subtitle', ''),
                emby_url=raw_config['email_template'].get('emby_url', ''),
                unsubscribe_email=raw_config['email_template'].get('unsubscribe_email', ''),
                emby_owner_name=raw_config['email_template'].get('emby_owner_name', '')
            )

            # Parse email configuration
            email_config = EmailConfig(
                smtp_server=raw_config['email']['smtp_server'],
                smtp_port=int(raw_config['email']['smtp_port']),
                smtp_username=raw_config['email']['smtp_username'],
                smtp_password=raw_config['email']['smtp_password'],
                smtp_sender_email=raw_config['email']['smtp_sender_email']
            )

            # Parse scheduler configuration (optional)
            scheduler_config = None
            if 'scheduler' in raw_config and raw_config['scheduler']:
                scheduler_config = SchedulerConfig(
                    cron=raw_config['scheduler'].get('cron')
                )

            # Parse recipients
            recipients = raw_config.get('recipients', [])

            return AppConfig(
                emby=emby_config,
                tmdb=tmdb_config,
                email_template=email_template_config,
                email=email_config,
                recipients=recipients,
                scheduler=scheduler_config
            )

        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid configuration value: {e}")

    def _validate_config(self, config: AppConfig) -> None:
        """Validate configuration values"""
        errors = []

        # Validate Emby configuration
        if not config.emby.url:
            errors.append("Emby URL is required")
        if not config.emby.api_token:
            errors.append("Emby API token is required")
        if config.emby.observed_period_days <= 0:
            errors.append("Observed period days must be greater than 0")

        # Validate TMDB configuration
        if not config.tmdb.api_key:
            errors.append("TMDB API key is required")

        # Validate email configuration
        if not config.email.smtp_server:
            errors.append("SMTP server is required")
        if not (1 <= config.email.smtp_port <= 65535):
            errors.append("SMTP port must be between 1 and 65535")
        if not config.email.smtp_username:
            errors.append("SMTP username is required")
        if not config.email.smtp_password:
            errors.append("SMTP password is required")
        if not config.email.smtp_sender_email:
            errors.append("SMTP sender email is required")

        # Validate email template configuration
        if config.email_template.language not in ['en', 'fr']:
            errors.append("Email template language must be 'en' or 'fr'")
        if not config.email_template.subject:
            errors.append("Email subject is required")
        if not config.email_template.title:
            errors.append("Email title is required")

        # Validate recipients
        if not config.recipients:
            errors.append("At least one recipient is required")

        # Validate scheduler configuration
        if config.scheduler and config.scheduler.cron:
            if not self._validate_cron_expression(config.scheduler.cron):
                errors.append("Invalid cron expression")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    def _validate_cron_expression(self, cron_expr: str) -> bool:
        """Validate cron expression format"""
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return False

            # Basic validation - could be more comprehensive
            for part in parts:
                if not (part.isdigit() or part == '*' or '/' in part or '-' in part or ',' in part):
                    return False

            return True
        except:
            return False

    def get_config(self) -> AppConfig:
        """Get the loaded configuration"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def reload_config(self) -> AppConfig:
        """Reload configuration from file"""
        return self.load_config()

    def get_emby_config(self) -> EmbyConfig:
        """Get Emby configuration"""
        return self.get_config().emby

    def get_tmdb_config(self) -> TMDBConfig:
        """Get TMDB configuration"""
        return self.get_config().tmdb

    def get_email_config(self) -> EmailConfig:
        """Get email configuration"""
        return self.get_config().email

    def get_email_template_config(self) -> EmailTemplateConfig:
        """Get email template configuration"""
        return self.get_config().email_template

    def get_scheduler_config(self) -> Optional[SchedulerConfig]:
        """Get scheduler configuration"""
        return self.get_config().scheduler

    def get_recipients(self) -> List[str]:
        """Get email recipients"""
        return self.get_config().recipients


# Global configuration manager instance
config_manager = ConfigurationManager()