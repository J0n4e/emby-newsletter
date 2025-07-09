#!/usr/bin/env python3
"""
Configuration checker for Emby Newsletter
Enhanced with proper timezone support
"""

import sys
import os
import logging
import requests
import smtplib
import ssl
import re
import time
import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from configuration import ConfigurationManager, AppConfig

logger = logging.getLogger(__name__)


def setup_timezone():
    """Set up timezone from environment variable"""
    tz_env = os.environ.get('TZ')
    if tz_env:
        try:
            os.environ['TZ'] = tz_env
            time.tzset()
            print(f"🌍 Timezone set to: {tz_env}")
        except Exception as e:
            print(f"⚠️  Warning: Could not set timezone: {e}")


class ConfigurationChecker:
    """Checks configuration validity and connectivity"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_all(self) -> bool:
        """Run all configuration checks"""
        logger.info("Starting configuration checks...")

        # Run all checks
        self.check_emby_connectivity()
        self.check_tmdb_connectivity()
        self.check_email_configuration()
        self.check_emby_folders()

        # Report results
        self._report_results()

        return len(self.errors) == 0

    def check_emby_connectivity(self) -> bool:
        """Test Emby server connectivity and API access"""
        logger.info("Checking Emby server connectivity...")

        try:
            # Test basic connectivity
            url = f"{self.config.emby.url}/emby/System/Info"
            headers = {
                'X-Emby-Token': self.config.emby.api_token,
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 401:
                self.errors.append("Emby API authentication failed. Check your API token.")
                return False
            elif response.status_code == 404:
                self.errors.append("Emby server not found. Check your Emby URL.")
                return False
            elif not response.ok:
                self.errors.append(f"Emby server returned error: {response.status_code}")
                return False

            # Check if we can access the system info
            system_info = response.json()
            server_name = system_info.get('ServerName', 'Unknown')
            version = system_info.get('Version', 'Unknown')

            logger.info(f"Connected to Emby server: {server_name} (v{version})")

            # Test Items endpoint access
            items_url = f"{self.config.emby.url}/emby/Items"
            items_response = requests.get(items_url, headers=headers, timeout=30)

            if not items_response.ok:
                self.warnings.append("Cannot access Emby Items endpoint. Newsletter may not work properly.")

            return True

        except requests.exceptions.ConnectionError:
            self.errors.append("Cannot connect to Emby server. Check URL and network connectivity.")
            return False
        except requests.exceptions.Timeout:
            self.errors.append("Emby server connection timed out.")
            return False
        except Exception as e:
            self.errors.append(f"Emby connectivity check failed: {e}")
            return False

    def check_tmdb_connectivity(self) -> bool:
        """Test TMDB API connectivity"""
        logger.info("Checking TMDB API connectivity...")

        try:
            url = "https://api.themoviedb.org/3/configuration"
            headers = {
                'Authorization': f'Bearer {self.config.tmdb.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 401:
                self.errors.append("TMDB API authentication failed. Check your API key.")
                return False
            elif not response.ok:
                self.errors.append(f"TMDB API returned error: {response.status_code}")
                return False

            logger.info("TMDB API connectivity successful")
            return True

        except requests.exceptions.ConnectionError:
            self.errors.append("Cannot connect to TMDB API. Check internet connectivity.")
            return False
        except requests.exceptions.Timeout:
            self.errors.append("TMDB API connection timed out.")
            return False
        except Exception as e:
            self.errors.append(f"TMDB connectivity check failed: {e}")
            return False

    def check_email_configuration(self) -> bool:
        """Test SMTP email configuration"""
        logger.info("Checking email configuration...")

        try:
            # Test SMTP connection with timeout
            context = ssl.create_default_context()

            with smtplib.SMTP(self.config.email.smtp_server, self.config.email.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.config.email.smtp_username, self.config.email.smtp_password)

            logger.info("SMTP configuration test successful")

            # Validate recipients
            if not self.config.recipients:
                self.errors.append("No email recipients configured.")
                return False

            # Email validation pattern
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

            for recipient in self.config.recipients:
                if not email_pattern.match(recipient.strip()):
                    self.warnings.append(f"Invalid email format: {recipient}")

            return True

        except smtplib.SMTPAuthenticationError:
            self.errors.append("SMTP authentication failed. Check username and password.")
            return False
        except smtplib.SMTPConnectError:
            self.errors.append("Cannot connect to SMTP server. Check server and port.")
            return False
        except smtplib.SMTPException as e:
            self.errors.append(f"SMTP error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Email configuration check failed: {e}")
            return False

    def check_emby_folders(self) -> bool:
        """Check if configured Emby folders exist and are accessible"""
        logger.info("Checking Emby folder configuration...")

        try:
            # Get library folders from Emby
            url = f"{self.config.emby.url}/emby/Library/VirtualFolders"
            headers = {
                'X-Emby-Token': self.config.emby.api_token,
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if not response.ok:
                self.warnings.append("Cannot access Emby library folders. Folder filtering may not work.")
                return False

            virtual_folders = response.json()
            available_folders = []

            for folder in virtual_folders:
                for location in folder.get('Locations', []):
                    folder_name = location.split('/')[-1].strip('/')
                    if folder_name:
                        available_folders.append(folder_name)

            # Check configured movie folders
            for folder in self.config.emby.watched_film_folders:
                if folder and folder not in available_folders:
                    self.warnings.append(f"Movie folder '{folder}' not found in Emby libraries.")

            # Check configured TV folders
            for folder in self.config.emby.watched_tv_folders:
                if folder and folder not in available_folders:
                    self.warnings.append(f"TV folder '{folder}' not found in Emby libraries.")

            if available_folders:
                logger.info(f"Available Emby folders: {', '.join(available_folders)}")
            else:
                self.warnings.append("No Emby library folders found.")

            return True

        except Exception as e:
            self.warnings.append(f"Could not check Emby folders: {e}")
            return False

    def check_recent_items(self) -> Tuple[int, int]:
        """Check how many recent items are available"""
        logger.info("Checking for recent items...")

        try:
            from datetime import datetime, timedelta

            # Calculate the date from observed_period_days ago
            since_date = datetime.now() - timedelta(days=self.config.emby.observed_period_days)

            url = f"{self.config.emby.url}/emby/Items"
            headers = {
                'X-Emby-Token': self.config.emby.api_token,
                'Content-Type': 'application/json'
            }

            params = {
                'IncludeItemTypes': 'Movie,Episode',
                'Recursive': 'true',
                'SortBy': 'DateCreated',
                'SortOrder': 'Descending',
                'Fields': 'DateCreated',
                'MinDateLastSaved': since_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.ok:
                data = response.json()
                items = data.get('Items', [])

                movies = len([item for item in items if item.get('Type') == 'Movie'])
                episodes = len([item for item in items if item.get('Type') == 'Episode'])

                logger.info(f"Found {movies} recent movies and {episodes} recent episodes")

                if movies == 0 and episodes == 0:
                    self.warnings.append(
                        f"No recent items found in the last {self.config.emby.observed_period_days} days.")

                return movies, episodes
            else:
                self.warnings.append("Could not retrieve recent items from Emby.")
                return 0, 0

        except Exception as e:
            self.warnings.append(f"Could not check recent items: {e}")
            return 0, 0

    def _report_results(self) -> None:
        """Report check results"""
        print("\n" + "=" * 60)
        print("CONFIGURATION CHECK RESULTS")
        print("=" * 60)

        if self.errors:
            print("\n❌ ERRORS (must be fixed):")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS (recommended to address):")
            for warning in self.warnings:
                print(f"   • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All checks passed! Configuration looks good.")
        elif not self.errors:
            print("\n✅ Configuration is valid, but there are warnings to consider.")
        else:
            print(f"\n❌ Configuration has {len(self.errors)} error(s) that must be fixed.")

        print("=" * 60 + "\n")


def main():
    """Main function for standalone configuration checking"""
    parser = argparse.ArgumentParser(description="Check Emby Newsletter configuration")
    parser.add_argument('-c', '--config',
                        default='/app/config/config.yml',
                        help='Path to configuration file')
    parser.add_argument('--no-connectivity',
                        action='store_true',
                        help='Skip connectivity checks')

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Set up timezone
        setup_timezone()

        # Display current time info
        current_time = datetime.now()
        current_tz = os.environ.get('TZ', 'UTC')

        print("=" * 60)
        print("EMBY NEWSLETTER - CONFIGURATION CHECK")
        print("=" * 60)
        print(f"🕐 Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 Timezone: {current_time.strftime('%Z')} ({current_tz})")
        print(f"📁 Config file: {args.config}")
        print("=" * 60)
        print()

        # Load configuration
        config_manager = ConfigurationManager(args.config)
        config = config_manager.load_config()

        # Run configuration checks
        checker = ConfigurationChecker(config)

        if args.no_connectivity:
            print("🔍 Running basic configuration validation only...")
            # Only run basic validation, no connectivity checks
            success = True
            print("✅ Basic configuration validation passed!")
        else:
            print("🔍 Running full configuration check...")
            success = checker.check_all()

            # Also check for recent items if connectivity checks passed
            if success:
                movies, episodes = checker.check_recent_items()
                print(f"📊 Recent content: {movies} movies, {episodes} episodes")

        if success:
            print()
            print("✅ Configuration check completed successfully!")
            print("🚀 Ready to run newsletter!")
            sys.exit(0)
        else:
            print()
            print("❌ Configuration check failed!")
            print("🔧 Please fix the errors above before running newsletter.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Configuration check failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()