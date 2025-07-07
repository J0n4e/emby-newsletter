#!/usr/bin/env python3
"""
Emby Newsletter - A newsletter for Emby to notify users of latest additions
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

# Import our configuration management and template renderer
from configuration import ConfigurationManager
from template_renderer import template_renderer

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
            return data.get('Items', [])

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
            # Get recent items
            days = self.config.emby.observed_period_days
            movie_folders = self.config.emby.watched_film_folders
            tv_folders = self.config.emby.watched_tv_folders

            # Get movies and TV shows separately
            recent_movies = []
            recent_tv_shows = []

            if movie_folders and movie_folders[0]:  # Check if not empty
                movie_items = self.emby_api.get_recent_items(days, movie_folders)
                recent_movies = [item for item in movie_items if item.get('Type') == 'Movie']

            if tv_folders and tv_folders[0]:  # Check if not empty
                tv_items = self.emby_api.get_recent_items(days, tv_folders)
                recent_tv_shows = [item for item in tv_items if item.get('Type') == 'Episode']

            # Process items and enhance with TMDB data
            processed_movies = self._process_movies(recent_movies)
            processed_tv_shows = self._process_tv_shows(recent_tv_shows)

            # Generate HTML content
            html_content = self._generate_html(processed_movies, processed_tv_shows)

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

            return template_renderer.render_email_template(context)

        except Exception as e:
            logger.error(f"Error generating HTML template: {e}")
            raise

    def send_newsletter(self, html_content: str) -> bool:
        """Send newsletter via email"""
        try:
            # Email configuration
            email_config = self.config.email
            recipients = self.config.recipients
            subject = self.config.email_template.subject

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

            logger.info(f"Newsletter sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending newsletter: {e}")
            return False_template
            ']['
            subject
            ']

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = ', '.join(recipients)

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipients, msg.as_string())

            logger.info(f"Newsletter sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending newsletter: {e}")
            return False


def main():
    """Main function"""
    try:
        logger.info("Starting Emby Newsletter")

        # Load configuration
        config_manager = ConfigurationManager()
        config_manager.load_config()

        # Generate and send newsletter
        generator = NewsletterGenerator(config_manager)
        html_content = generator.generate_newsletter()

        if html_content:
            success = generator.send_newsletter(html_content)
            if success:
                logger.info("Newsletter generation and sending completed successfully")
            else:
                logger.error("Failed to send newsletter")
                sys.exit(1)
        else:
            logger.error("Failed to generate newsletter")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()