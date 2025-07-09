#!/usr/bin/env python3
"""
Emby Newsletter - A newsletter for Emby to notify users of latest additions
"""

import sys
import os
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

# Import our configuration management and template renderer
from configuration import ConfigurationManager
from template_renderer import render_email_with_server_stats


def log_timezone_debug():
    """Log comprehensive timezone and time information for debugging"""

    print("=" * 80)
    print("EMBY NEWSLETTER - TIMEZONE AND TIME DEBUG INFORMATION")
    print("=" * 80)

    # System time information
    print("📅 SYSTEM TIME INFO:")
    print(f"   Current UTC time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Current local time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   System timezone names: {time.tzname}")
    print(f"   Timezone offset from UTC: {time.timezone} seconds ({time.timezone / 3600:.1f} hours)")
    print(f"   Daylight saving time active: {'Yes' if time.daylight else 'No'}")
    if time.daylight:
        print(f"   DST timezone offset: {time.altzone} seconds ({time.altzone / 3600:.1f} hours)")
    print()

    # Environment variables
    print("🌍 ENVIRONMENT VARIABLES:")
    print(f"   TZ: {os.environ.get('TZ', 'Not set')}")
    print(f"   LANG: {os.environ.get('LANG', 'Not set')}")
    print(f"   LC_TIME: {os.environ.get('LC_TIME', 'Not set')}")
    print(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()

    # System timezone files and configuration
    print("📁 SYSTEM TIMEZONE FILES:")
    try:
        with open('/etc/timezone', 'r') as f:
            timezone_content = f.read().strip()
            print(f"   /etc/timezone: {timezone_content}")
    except FileNotFoundError:
        print("   /etc/timezone: File not found")
    except Exception as e:
        print(f"   /etc/timezone: Error reading - {e}")

    try:
        if os.path.islink('/etc/localtime'):
            link_target = os.readlink('/etc/localtime')
            print(f"   /etc/localtime: Symlink to {link_target}")
            # Extract timezone from symlink path
            if '/zoneinfo/' in link_target:
                tz_from_link = link_target.split('/zoneinfo/')[-1]
                print(f"   Timezone from symlink: {tz_from_link}")
        else:
            print("   /etc/localtime: Regular file (not a symlink)")
    except Exception as e:
        print(f"   /etc/localtime: Error checking - {e}")

    print()

    # Python timezone detection
    print("🐍 PYTHON TIMEZONE INFO:")
    try:
        # Try different methods to detect timezone
        import time
        import datetime

        # Method 1: time.tzname
        print(f"   time.tzname: {time.tzname}")

        # Method 2: datetime timezone
        now = datetime.now()
        print(f"   datetime.now(): {now}")

        # Method 3: Check if zoneinfo is available (Python 3.9+)
        try:
            from zoneinfo import ZoneInfo
            if 'TZ' in os.environ:
                tz = ZoneInfo(os.environ['TZ'])
                now_with_tz = datetime.now(tz)
                print(f"   datetime with TZ env: {now_with_tz}")
                print(f"   ZoneInfo timezone: {tz}")
        except ImportError:
            print("   zoneinfo module not available (Python < 3.9)")
        except Exception as e:
            print(f"   zoneinfo error: {e}")

        # Method 4: Try pytz if available
        try:
            import pytz
            if 'TZ' in os.environ:
                tz_pytz = pytz.timezone(os.environ['TZ'])
                now_pytz = datetime.now(tz_pytz)
                print(f"   pytz datetime: {now_pytz}")
                print(f"   pytz timezone: {tz_pytz}")
        except ImportError:
            print("   pytz module not available")
        except Exception as e:
            print(f"   pytz error: {e}")

    except Exception as e:
        print(f"   Python timezone detection error: {e}")

    print()

    # System date commands
    print("🕐 SYSTEM DATE COMMANDS:")
    try:
        result = subprocess.run(['date'], capture_output=True, text=True, timeout=5)
        print(f"   'date' command: {result.stdout.strip()}")
    except Exception as e:
        print(f"   'date' command error: {e}")

    try:
        result = subprocess.run(['date', '-u'], capture_output=True, text=True, timeout=5)
        print(f"   'date -u' command: {result.stdout.strip()}")
    except Exception as e:
        print(f"   'date -u' command error: {e}")

    try:
        result = subprocess.run(['date', '+%Z %z'], capture_output=True, text=True, timeout=5)
        print(f"   timezone info: {result.stdout.strip()}")
    except Exception as e:
        print(f"   timezone info error: {e}")

    print()

    # Process and container information
    print("🐳 CONTAINER INFO:")
    print(f"   Working directory: {os.getcwd()}")
    print(f"   User ID: {os.getuid()}")
    print(f"   Group ID: {os.getgid()}")
    print(f"   Process ID: {os.getpid()}")
    print()

    # Cron daemon status
    print("⏰ CRON DAEMON STATUS:")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        cron_processes = [line for line in lines if any(
            word in line.lower() for word in ['cron', 'crond']) and 'grep' not in line and line.strip()]

        if cron_processes:
            print("   Cron processes found:")
            for process in cron_processes:
                print(f"     {process.strip()}")
        else:
            print("   ❌ No cron processes found")
    except Exception as e:
        print(f"   Process check error: {e}")

    # Check crontab entries
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            print("   Current crontab entries:")
            for line in result.stdout.strip().split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    print(f"     {line.strip()}")
        else:
            print("   ❌ No crontab entries found")
    except Exception as e:
        print(f"   Crontab check error: {e}")

    # Check for cron logs
    cron_log_files = ['/var/log/cron.log', '/var/log/cron', '/var/log/emby-newsletter.log']
    print("   Checking for cron log files:")
    for log_file in cron_log_files:
        if os.path.exists(log_file):
            try:
                stat_info = os.stat(log_file)
                print(f"     ✅ {log_file} (size: {stat_info.st_size} bytes)")
                # Show last few lines if file is not too large
                if stat_info.st_size < 10000:  # Less than 10KB
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                print(f"        Last few lines:")
                                for line in lines[-3:]:
                                    print(f"          {line.strip()}")
                    except Exception as read_e:
                        print(f"        Error reading file: {read_e}")
            except Exception as stat_e:
                print(f"     ❌ {log_file} (error: {stat_e})")
        else:
            print(f"     ❌ {log_file} (not found)")

    print()

    # Expected vs actual time comparison
    print("🎯 TIME COMPARISON:")
    if 'TZ' in os.environ:
        try:
            expected_tz = os.environ['TZ']
            print(f"   Expected timezone: {expected_tz}")

            # Try to show what time it should be in that timezone
            result = subprocess.run(['date'], capture_output=True, text=True, timeout=5)
            current_time = result.stdout.strip()
            print(f"   Current container time: {current_time}")

            # Show what time it should be in expected timezone
            try:
                result = subprocess.run(['env', f'TZ={expected_tz}', 'date'], capture_output=True, text=True, timeout=5)
                expected_time = result.stdout.strip()
                print(f"   Expected time in {expected_tz}: {expected_time}")
            except Exception:
                print(f"   Could not calculate expected time for {expected_tz}")

        except Exception as e:
            print(f"   Time comparison error: {e}")
    else:
        print("   ❌ TZ environment variable not set")

    print("=" * 80)
    print("END TIMEZONE DEBUG - Starting newsletter execution...")
    print("=" * 80)
    print()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbyAPI:
    """Handles communication with Emby server"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Emby-Token': api_key,
            'Content-Type': 'application/json'
        })

    def get_recent_items(self, days: int = 30, folders: List[str] = None) -> List[Dict]:
        """Get recently added items from Emby"""
        try:
            # Calculate the date from days ago
            since_date = datetime.now() - timedelta(days=days)
            logger.info(f"Fetching items added since: {since_date.strftime('%Y-%m-%d %H:%M:%S')}")

            # Get all items added since the specified date
            params = {
                'IncludeItemTypes': 'Movie,Episode',
                'Recursive': 'true',
                'SortBy': 'DateCreated',
                'SortOrder': 'Descending',
                'Fields': 'DateCreated,ParentId,SeriesName,SeasonName,IndexNumber,ParentIndexNumber,Overview,Genres,ProductionYear,CommunityRating,OfficialRating',
                'MinDateLastSaved': since_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            }

            if folders:
                # Get folder IDs for the specified folder names
                folder_ids = self._get_folder_ids(folders)
                if folder_ids:
                    params['ParentIds'] = ','.join(folder_ids)

            url = f"{self.base_url}/emby/Items"
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get('Items', [])
            logger.info(f"Found {len(items)} recent items")
            return items

        except Exception as e:
            logger.error(f"Error fetching recent items from Emby: {e}")
            return []

    def _get_folder_ids(self, folder_names: List[str]) -> List[str]:
        """Get folder IDs for given folder names"""
        try:
            url = f"{self.base_url}/emby/Library/VirtualFolders"
            response = self.session.get(url)
            response.raise_for_status()

            folders = response.json()
            folder_ids = []

            for folder in folders:
                for location in folder.get('Locations', []):
                    folder_name = os.path.basename(location.rstrip('/'))
                    if folder_name in folder_names:
                        # Get the library ID
                        lib_url = f"{self.base_url}/emby/Library/MediaFolders"
                        lib_response = self.session.get(lib_url)
                        lib_response.raise_for_status()

                        for lib_folder in lib_response.json().get('Items', []):
                            if any(location in loc for loc in lib_folder.get('Locations', [])):
                                folder_ids.append(lib_folder['Id'])
                                break

            return folder_ids

        except Exception as e:
            logger.error(f"Error getting folder IDs: {e}")
            return []

    def get_item_image_url(self, item_id: str, image_type: str = 'Primary') -> Optional[str]:
        """Get image URL for an item"""
        try:
            return f"{self.base_url}/emby/Items/{item_id}/Images/{image_type}"
        except Exception as e:
            logger.error(f"Error getting image URL for item {item_id}: {e}")
            return None


class TMDBApi:
    """Handles communication with TMDB API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def get_movie_details(self, title: str, year: int = None) -> Optional[Dict]:
        """Get movie details from TMDB"""
        try:
            params = {'query': title}
            if year:
                params['year'] = year

            url = f"{self.base_url}/search/movie"
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if results:
                return results[0]  # Return first match

        except Exception as e:
            logger.error(f"Error fetching movie details from TMDB: {e}")

        return None

    def get_tv_details(self, title: str, year: int = None) -> Optional[Dict]:
        """Get TV show details from TMDB"""
        try:
            params = {'query': title}
            if year:
                params['first_air_date_year'] = year

            url = f"{self.base_url}/search/tv"
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if results:
                return results[0]  # Return first match

        except Exception as e:
            logger.error(f"Error fetching TV details from TMDB: {e}")

        return None


class NewsletterGenerator:
    """Generates and sends newsletters"""

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.emby_api = EmbyAPI(
            self.config.emby.url,
            self.config.emby.api_token
        )
        self.tmdb_api = TMDBApi(self.config.tmdb.api_key)

    def generate_newsletter(self) -> Optional[str]:
        """Generate newsletter content"""
        try:
            logger.info("Starting newsletter generation...")

            # Get recent items
            days = self.config.emby.observed_period_days
            movie_folders = self.config.emby.watched_film_folders
            tv_folders = self.config.emby.watched_tv_folders

            logger.info(f"Looking for content added in the last {days} days")
            logger.info(f"Movie folders: {movie_folders}")
            logger.info(f"TV folders: {tv_folders}")

            # Get movies and TV shows separately
            recent_movies = []
            recent_tv_shows = []

            if movie_folders and movie_folders[0]:  # Check if not empty
                movie_items = self.emby_api.get_recent_items(days, movie_folders)
                recent_movies = [item for item in movie_items if item.get('Type') == 'Movie']
                logger.info(f"Found {len(recent_movies)} recent movies")

            if tv_folders and tv_folders[0]:  # Check if not empty
                tv_items = self.emby_api.get_recent_items(days, tv_folders)
                recent_tv_shows = [item for item in tv_items if item.get('Type') == 'Episode']
                logger.info(f"Found {len(recent_tv_shows)} recent TV episodes")

            # Process items and enhance with TMDB data
            processed_movies = self._process_movies(recent_movies)
            processed_tv_shows = self._process_tv_shows(recent_tv_shows)

            # Generate HTML content
            html_content = self._generate_html(processed_movies, processed_tv_shows)

            logger.info("Newsletter generation completed successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error generating newsletter: {e}")
            return None

    def _process_movies(self, movies: List[Dict]) -> List[Dict]:
        """Process movie items and enhance with TMDB data"""
        processed = []

        for movie in movies:
            try:
                # Extract movie info
                title = movie.get('Name', '')
                year = movie.get('ProductionYear')

                # Get TMDB details
                tmdb_data = self.tmdb_api.get_movie_details(title, year)

                processed_movie = {
                    'title': title,
                    'year': year,
                    'overview': movie.get('Overview', ''),
                    'genres': movie.get('Genres', []),
                    'rating': movie.get('CommunityRating'),
                    'official_rating': movie.get('OfficialRating'),
                    'date_added': movie.get('DateCreated'),
                    'emby_id': movie.get('Id'),
                    'poster_url': self.emby_api.get_item_image_url(movie.get('Id', ''))
                }

                # Enhance with TMDB data
                if tmdb_data:
                    processed_movie.update({
                        'tmdb_overview': tmdb_data.get('overview', ''),
                        'tmdb_poster': f"https://image.tmdb.org/t/p/w500{tmdb_data.get('poster_path', '')}" if tmdb_data.get(
                            'poster_path') else None,
                        'tmdb_rating': tmdb_data.get('vote_average'),
                        'tmdb_genres': [g.get('name') for g in tmdb_data.get('genres', [])]
                    })

                processed.append(processed_movie)

            except Exception as e:
                logger.error(f"Error processing movie {movie.get('Name', 'Unknown')}: {e}")

        return processed

    def _process_tv_shows(self, episodes: List[Dict]) -> List[Dict]:
        """Process TV show episodes and group by series"""
        series_dict = {}

        for episode in episodes:
            try:
                series_name = episode.get('SeriesName', '')
                season_name = episode.get('SeasonName', '')
                episode_name = episode.get('Name', '')

                if series_name not in series_dict:
                    # Get TMDB details for the series
                    year = episode.get('ProductionYear')
                    tmdb_data = self.tmdb_api.get_tv_details(series_name, year)

                    series_dict[series_name] = {
                        'title': series_name,
                        'seasons': {},
                        'tmdb_data': tmdb_data,
                        'poster_url': self.emby_api.get_item_image_url(episode.get('SeriesId', ''))
                    }

                if season_name not in series_dict[series_name]['seasons']:
                    series_dict[series_name]['seasons'][season_name] = []

                series_dict[series_name]['seasons'][season_name].append({
                    'name': episode_name,
                    'episode_number': episode.get('IndexNumber'),
                    'season_number': episode.get('ParentIndexNumber'),
                    'date_added': episode.get('DateCreated'),
                    'overview': episode.get('Overview', '')
                })

            except Exception as e:
                logger.error(f"Error processing episode {episode.get('Name', 'Unknown')}: {e}")

        return list(series_dict.values())

    def _generate_html(self, movies: List[Dict], tv_shows: List[Dict]) -> str:
        """Generate HTML newsletter content using secure template rendering"""
        try:
            context = {
                'language': self.config.email_template.language,
                'title': self.config.email_template.title,
                'subtitle': self.config.email_template.subtitle,
                'movies': movies,
                'tv_shows': tv_shows,
                'emby_url': self.config.email_template.emby_url,
                'emby_owner_name': self.config.email_template.emby_owner_name,
                'unsubscribe_email': self.config.email_template.unsubscribe_email
            }

            # Use the new function that automatically fetches server statistics
            return render_email_with_server_stats(context, config_path="/app/config/config.yml")

        except Exception as e:
            logger.error(f"Error generating HTML template: {e}")
            raise

    def send_newsletter(self, html_content: str) -> bool:
        """Send newsletter via email"""
        try:
            logger.info("Starting email send process...")

            # Email configuration
            email_config = self.config.email
            recipients = self.config.recipients
            subject = self.config.email_template.subject

            logger.info(f"Sending to {len(recipients)} recipients: {recipients}")
            logger.info(f"Using SMTP server: {email_config.smtp_server}:{email_config.smtp_port}")

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config.smtp_sender_email
            msg['To'] = ', '.join(recipients)

            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Send email with timeout
            context = ssl.create_default_context()
            with smtplib.SMTP(email_config.smtp_server, email_config.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(email_config.smtp_username, email_config.smtp_password)
                server.sendmail(email_config.smtp_sender_email, recipients, msg.as_string())

            logger.info(f"✅ Newsletter sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending newsletter: {e}")
            return False


def main():
    """Main function"""
    try:
        # Run timezone debugging first
        log_timezone_debug()

        logger.info("🚀 Starting Emby Newsletter")

        # Load configuration
        config_manager = ConfigurationManager()
        config_manager.load_config()

        # Generate and send newsletter
        generator = NewsletterGenerator(config_manager)
        html_content = generator.generate_newsletter()

        if html_content:
            success = generator.send_newsletter(html_content)
            if success:
                logger.info("✅ Newsletter generation and sending completed successfully")
                print("=" * 80)
                print("🎉 NEWSLETTER COMPLETED SUCCESSFULLY!")
                print(f"📧 Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
            else:
                logger.error("❌ Failed to send newsletter")
                sys.exit(1)
        else:
            logger.error("❌ Failed to generate newsletter")
            sys.exit(1)

    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        print("=" * 80)
        print("❌ NEWSLETTER FAILED!")
        print(f"💥 Error: {e}")
        print(f"🕐 Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()