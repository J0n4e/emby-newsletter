#!/usr/bin/env python3
"""
Emby Newsletter - A newsletter for Emby to notify users of latest additions
Enhanced with proper timezone support and fixed poster matching
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


def setup_timezone():
    """Set up timezone from environment variable"""
    tz_env = os.environ.get('TZ')
    if tz_env:
        try:
            # Set timezone for Python
            os.environ['TZ'] = tz_env
            time.tzset()
            print(f"🌍 Python timezone set to: {tz_env}")
        except Exception as e:
            print(f"⚠️  Warning: Could not set Python timezone: {e}")
    else:
        print("⚠️  No TZ environment variable found")


def comprehensive_timezone_debug():
    """Comprehensive timezone debugging with all relevant information"""
    print("=" * 80)
    print("EMBY NEWSLETTER - TIMEZONE DEBUG")
    print("=" * 80)

    # Setup timezone first
    setup_timezone()

    # Basic time info
    now_local = datetime.now()
    now_utc = datetime.utcnow()

    print(f"📅 CURRENT TIME INFO:")
    print(f"   Local time: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Calculate time difference
    time_diff = (now_local - now_utc).total_seconds() / 3600
    print(f"   Time difference: {time_diff:+.1f} hours from UTC")
    print()

    # Environment variables
    print(f"🌍 ENVIRONMENT:")
    print(f"   TZ variable: {os.environ.get('TZ', 'Not set')}")
    print(f"   LANG: {os.environ.get('LANG', 'Not set')}")
    print(f"   LC_TIME: {os.environ.get('LC_TIME', 'Not set')}")
    print()

    # System timezone info
    print(f"⏰ SYSTEM TIMEZONE:")
    print(f"   Python timezone names: {time.tzname}")
    print(f"   Timezone offset: {time.timezone} seconds ({time.timezone / 3600:.1f} hours)")
    print(f"   DST active: {'Yes' if time.daylight else 'No'}")

    # Additional timezone info
    try:
        if hasattr(time, 'altzone'):
            print(f"   Alternative timezone: {time.altzone} seconds")
    except:
        pass
    print()

    # System commands
    print(f"🖥️ SYSTEM DATE:")
    try:
        date_result = subprocess.run(['date'], capture_output=True, text=True, timeout=5)
        if date_result.returncode == 0:
            print(f"   System date: {date_result.stdout.strip()}")
        else:
            print(f"   System date: Error getting date")
    except Exception as e:
        print(f"   System date: Error - {e}")

    try:
        date_utc_result = subprocess.run(['date', '-u'], capture_output=True, text=True, timeout=5)
        if date_utc_result.returncode == 0:
            print(f"   System UTC: {date_utc_result.stdout.strip()}")
    except Exception as e:
        print(f"   System UTC: Error - {e}")

    print()

    # Timezone files
    print(f"📁 TIMEZONE CONFIG:")
    try:
        with open('/etc/timezone', 'r') as f:
            tz_content = f.read().strip()
            print(f"   /etc/timezone: {tz_content}")
    except FileNotFoundError:
        print(f"   /etc/timezone: Not found")
    except Exception as e:
        print(f"   /etc/timezone: Error - {e}")

    try:
        if os.path.islink('/etc/localtime'):
            link = os.readlink('/etc/localtime')
            print(f"   /etc/localtime: {link}")
        else:
            print(f"   /etc/localtime: Regular file (not symlink)")
    except Exception as e:
        print(f"   /etc/localtime: Error - {e}")

    print()

    # Container info
    print(f"🐳 CONTAINER:")
    print(f"   Working dir: {os.getcwd()}")
    print(f"   User: {os.getuid()}:{os.getgid()}")
    print()

    # Cron status
    print(f"⏰ CRON STATUS:")
    try:
        ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        if ps_result.returncode == 0:
            cron_lines = [line for line in ps_result.stdout.split('\n')
                          if 'cron' in line.lower() and 'grep' not in line and line.strip()]
            if cron_lines:
                print(f"   Cron processes: {len(cron_lines)} found")
                for line in cron_lines[:2]:  # Show first 2
                    print(f"     {line.strip()}")
            else:
                print(f"   Cron processes: None found")
    except Exception as e:
        print(f"   Cron processes: Error - {e}")

    # Crontab entries
    try:
        crontab_result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
        if crontab_result.returncode == 0 and crontab_result.stdout.strip():
            lines = [line.strip() for line in crontab_result.stdout.strip().split('\n')
                     if line.strip() and not line.strip().startswith('#')]
            if lines:
                print(f"   Crontab entries:")
                for line in lines:
                    print(f"     {line}")
            else:
                print(f"   Crontab entries: None active")
        else:
            print(f"   Crontab entries: None found")
    except Exception as e:
        print(f"   Crontab entries: Error - {e}")

    # Python datetime tests
    print()
    print(f"🐍 PYTHON DATETIME:")
    try:
        print(f"   datetime.now(): {datetime.now()}")
        print(f"   datetime.utcnow(): {datetime.utcnow()}")

        # Test timezone-aware datetime
        try:
            from datetime import timezone
            utc_now = datetime.now(timezone.utc)
            print(f"   datetime.now(timezone.utc): {utc_now}")
        except Exception as e:
            print(f"   timezone.utc error: {e}")

        # Test time formatting
        test_time = datetime.now()
        print(f"   Formatted time: {test_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    except Exception as e:
        print(f"   Python datetime error: {e}")

    print("=" * 80)
    print("END TIMEZONE DEBUG")
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
                'Fields': 'DateCreated,ParentId,SeriesName,SeasonName,IndexNumber,ParentIndexNumber,Overview,Genres,ProductionYear,CommunityRating,OfficialRating,SeriesId',
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

    def get_series_info(self, series_id: str) -> Optional[Dict]:
        """Get detailed series information from Emby"""
        try:
            url = f"{self.base_url}/emby/Items/{series_id}"
            params = {
                'Fields': 'Overview,Genres,ProductionYear,CommunityRating,OfficialRating'
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching series info for {series_id}: {e}")
            return None

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
            if not item_id or item_id == '':
                return None
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
                # Find best match by title similarity
                best_match = None
                best_score = 0

                for result in results[:3]:  # Check top 3 results
                    result_title = result.get('title', '').lower()
                    search_title = title.lower()

                    # Simple similarity check
                    if result_title == search_title:
                        return result  # Exact match
                    elif search_title in result_title or result_title in search_title:
                        score = len(search_title) / max(len(result_title), 1)
                        if score > best_score:
                            best_score = score
                            best_match = result

                return best_match or results[0]  # Return best match or first result

        except Exception as e:
            logger.error(f"Error fetching movie details from TMDB for '{title}': {e}")

        return None

    def get_tv_details(self, title: str, year: int = None) -> Optional[Dict]:
        """Get TV show details from TMDB with improved matching"""
        try:
            # First, try exact search with year if available
            if year:
                params = {
                    'query': title,
                    'first_air_date_year': year
                }

                url = f"{self.base_url}/search/tv"
                response = self.session.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                results = data.get('results', [])

                # Look for exact title match first
                for result in results:
                    result_title = result.get('name', '').lower()
                    search_title = title.lower()
                    result_year = None

                    # Extract year from first_air_date
                    if result.get('first_air_date'):
                        try:
                            result_year = int(result['first_air_date'][:4])
                        except:
                            pass

                    # Exact match with year validation
                    if (result_title == search_title and
                            result_year and abs(result_year - year) <= 1):  # Allow 1 year difference
                        logger.info(
                            f"✅ Exact TMDB match with year for '{title}' ({year}): {result.get('name')} ({result_year})")
                        return result

            # Second attempt: Search without year constraint
            params = {'query': title}
            url = f"{self.base_url}/search/tv"
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if results:
                # Find best match by title similarity and popularity
                best_match = None
                best_score = 0

                for result in results[:5]:  # Check top 5 results
                    result_title = result.get('name', '').lower()
                    search_title = title.lower()
                    popularity = result.get('popularity', 0)

                    # Calculate similarity score
                    if result_title == search_title:
                        score = 100  # Perfect match
                    elif search_title in result_title:
                        score = 80 + (popularity / 100)  # Partial match + popularity bonus
                    elif result_title in search_title:
                        score = 60 + (popularity / 100)  # Contains search term + popularity
                    else:
                        # Check for word overlap
                        search_words = set(search_title.split())
                        result_words = set(result_title.split())
                        overlap = len(search_words.intersection(result_words))
                        if overlap > 0:
                            score = 40 + (overlap * 10) + (popularity / 100)
                        else:
                            score = popularity / 100  # Just popularity

                    # Add year bonus if available and matches
                    if year and result.get('first_air_date'):
                        try:
                            result_year = int(result['first_air_date'][:4])
                            if abs(result_year - year) <= 1:
                                score += 20  # Year match bonus
                        except:
                            pass

                    if score > best_score:
                        best_score = score
                        best_match = result

                if best_match:
                    result_year = "Unknown"
                    if best_match.get('first_air_date'):
                        try:
                            result_year = best_match['first_air_date'][:4]
                        except:
                            pass

                    logger.info(
                        f"✅ Best TMDB match for '{title}': {best_match.get('name')} ({result_year}) [score: {best_score:.1f}]")
                    return best_match
                else:
                    logger.warning(
                        f"⚠️ No good TMDB match found for '{title}' - using first result: {results[0].get('name')}")
                    return results[0]  # Fallback to first result

        except Exception as e:
            logger.error(f"Error fetching TV details from TMDB for '{title}': {e}")

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
        """Process movie items using Emby posters directly"""
        processed = []

        for movie in movies:
            try:
                # Extract movie info
                title = movie.get('Name', '')
                year = movie.get('ProductionYear')
                movie_id = movie.get('Id', '')

                logger.info(f"Processing movie: {title} ({year}) - ID: {movie_id}")

                # Use Emby poster directly - no TMDB needed
                emby_poster = self.emby_api.get_item_image_url(movie_id) if movie_id else None

                processed_movie = {
                    'title': title,
                    'year': year,
                    'overview': movie.get('Overview', ''),
                    'genres': movie.get('Genres', []),
                    'rating': movie.get('CommunityRating'),
                    'official_rating': movie.get('OfficialRating'),
                    'date_added': movie.get('DateCreated'),
                    'emby_id': movie_id,
                    'poster_url': emby_poster,
                    'poster_source': 'emby_direct'
                }

                if emby_poster:
                    logger.info(f"✅ Using Emby poster for {title}: {emby_poster}")
                else:
                    logger.warning(f"⚠️ No Emby poster found for {title}")

                processed.append(processed_movie)

            except Exception as e:
                logger.error(f"Error processing movie {movie.get('Name', 'Unknown')}: {e}")

        return processed

    def _process_tv_shows(self, episodes: List[Dict]) -> List[Dict]:
        """Process TV show episodes and group by series using Emby posters and descriptions"""
        series_dict = {}

        for episode in episodes:
            try:
                series_name = episode.get('SeriesName', '')
                season_name = episode.get('SeasonName', '')
                episode_name = episode.get('Name', '')
                series_id = episode.get('SeriesId', '')

                logger.info(f"Processing episode: {series_name} - {season_name} - {episode_name}")
                logger.info(f"Series ID: {series_id}")

                if series_name not in series_dict:
                    # Get series info from Emby for description and other details
                    series_info = None
                    series_overview = ""
                    series_genres = []
                    series_year = None
                    series_rating = None

                    if series_id:
                        series_info = self.emby_api.get_series_info(series_id)
                        if series_info:
                            series_overview = series_info.get('Overview', '')
                            series_genres = series_info.get('Genres', [])
                            series_year = series_info.get('ProductionYear')
                            series_rating = series_info.get('CommunityRating')
                            logger.info(f"✅ Got series info from Emby for {series_name}:")
                            logger.info(f"   Overview: {len(series_overview)} chars")
                            logger.info(f"   Genres: {series_genres}")
                            logger.info(f"   Year: {series_year}")
                            logger.info(f"   Rating: {series_rating}")

                    # Use Emby poster directly
                    emby_poster = None
                    poster_source = "none"

                    if series_id:
                        emby_poster = self.emby_api.get_item_image_url(series_id)
                        if emby_poster:
                            poster_source = "emby_direct"
                            logger.info(f"✅ Using Emby poster for {series_name}: {emby_poster}")
                        else:
                            logger.warning(f"⚠️ No Emby poster found for {series_name} (ID: {series_id})")
                    else:
                        logger.warning(f"⚠️ No Series ID found for {series_name}")

                    series_dict[series_name] = {
                        'title': series_name,
                        'seasons': {},
                        'poster_url': emby_poster,
                        'poster_source': poster_source,
                        'series_id': series_id,
                        'overview': series_overview,  # This should be used in template
                        'genres': series_genres,  # Add genres like movies
                        'year': series_year,  # Add year like movies
                        'rating': series_rating,  # Add rating like movies
                        'official_rating': series_info.get('OfficialRating') if series_info else None,
                        'tmdb_data': None  # Keep for template compatibility but don't use TMDB
                    }

                    logger.info(f"📺 Series created: {series_name}")
                    logger.info(f"   Poster: {poster_source}")
                    logger.info(f"   Overview: {len(series_overview)} chars")
                    logger.info(f"   Genres: {len(series_genres)} items")

                # Add episode to season
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

        # Log final results
        logger.info("=" * 50)
        logger.info("FINAL TV SHOW PROCESSING RESULTS (EMBY DIRECT):")
        for series_name, series_data in series_dict.items():
            poster_info = f"{series_data['poster_source']}: {series_data['poster_url'][:60]}..." if series_data['poster_url'] else "none"
            overview_info = f"{len(series_data.get('overview', ''))} chars" if series_data.get('overview') else "no overview"
            genres_info = f"{len(series_data.get('genres', []))} genres" if series_data.get('genres') else "no genres"
            year_info = f"year: {series_data.get('year', 'N/A')}"
            logger.info(f"  📺 {series_name}: {poster_info} | {overview_info} | {genres_info} | {year_info}")
        logger.info("=" * 50)

        return list(series_dict.values())

    def _generate_html(self, movies: List[Dict], tv_shows: List[Dict]) -> str:
        """Generate HTML newsletter content using secure template rendering"""
        try:
            # DEBUG: Print actual data being passed to template
            print("\n=== DEBUG: TV SHOWS POSTER DATA ===")
            for i, show in enumerate(tv_shows):
                print(f"Show {i}: {show.get('title')}")
                print(f"  poster_url: {show.get('poster_url')}")
                print(f"  poster_source: {show.get('poster_source')}")
                print(f"  overview: {len(show.get('overview', ''))} chars")
                print(f"  genres: {show.get('genres')}")
                print(f"  year: {show.get('year')}")
                print(f"  tmdb_data type: {type(show.get('tmdb_data'))}")
                if show.get('tmdb_data'):
                    print(f"  tmdb_data.poster_path: {show.get('tmdb_data', {}).get('poster_path')}")
                print(f"  ALL KEYS: {list(show.keys())}")
                print("---")
            print("=== END DEBUG ===\n")

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
    """Main function with proper timezone handling"""
    try:
        # Set up timezone first
        setup_timezone()

        # Run comprehensive timezone debugging
        comprehensive_timezone_debug()

        # Get timezone info for logging
        current_tz = os.environ.get('TZ', 'UTC')
        logger.info(f"🚀 Starting Emby Newsletter (Timezone: {current_tz})")

        # Load configuration
        config_manager = ConfigurationManager()
        config_manager.load_config()

        # Generate and send newsletter
        generator = NewsletterGenerator(config_manager)
        html_content = generator.generate_newsletter()

        if html_content:
            success = generator.send_newsletter(html_content)
            if success:
                current_time = datetime.now()
                logger.info("✅ Newsletter generation and sending completed successfully")
                print("=" * 80)
                print("🎉 NEWSLETTER COMPLETED SUCCESSFULLY!")
                print(f"📧 Sent at: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"🌍 Timezone: {current_time.strftime('%Z')} ({current_tz})")
                print(f"⏰ Local time: {current_time}")
                print("=" * 80)
            else:
                logger.error("❌ Failed to send newsletter")
                sys.exit(1)
        else:
            logger.error("❌ Failed to generate newsletter")
            sys.exit(1)

    except Exception as e:
        current_time = datetime.now()
        current_tz = os.environ.get('TZ', 'UTC')
        logger.error(f"💥 Unexpected error: {e}")
        print("=" * 80)
        print("❌ NEWSLETTER FAILED!")
        print(f"💥 Error: {e}")
        print(f"🕐 Failed at: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 Timezone: {current_time.strftime('%Z')} ({current_tz})")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()