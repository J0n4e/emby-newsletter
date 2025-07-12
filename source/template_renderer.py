#!/usr/bin/env python3
"""
Enhanced Template rendering for Emby Newsletter with metadata badges
Based on the original email_template.py implementation with visual enhancements
"""

import os
import logging
import html
import re
import yaml
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Translation dictionary - EXACT same as original
translation = {
    "en": {
        "discover_now": "Discover now",
        "new_film": "New movies:",
        "new_tvs": "New shows:",
        "currently_available": "Currently available in Emby:",
        "movies_label": "Movies",
        "episodes_label": "Episodes",
        "footer_label": "You are receiving this email because you are using ${emby_owner_name}'s Emby server. If you want to stop receiving these emails, you can unsubscribe by notifying ${unsubscribe_email}.",
        "added_on": "Added on"
    },
    "fr": {
        "discover_now": "Découvrir maintenant",
        "new_film": "Nouveaux films :",
        "new_tvs": "Nouvelles séries :",
        "currently_available": "Actuellement disponible sur Emby :",
        "movies_label": "Films",
        "episodes_label": "Épisodes",
        "footer_label": "Vous recevez cet email car vous utilisez le serveur Emby de ${emby_owner_name}. Si vous ne souhaitez plus recevoir ces emails, vous pouvez vous désinscrire en notifiant ${unsubscribe_email}.",
        "added_on": "Ajouté le"
    }
}


def get_metadata_badges(item_data: Dict[str, Any]) -> str:
    """Generate metadata badges HTML for movies and TV shows"""
    badges_html = ""
    
    # Year badge (blue) - extract from various possible fields
    year = item_data.get('year', item_data.get('release_year', ''))
    
    # Check for TMDB data structure
    if not year and 'tmdb_data' in item_data:
        tmdb = item_data['tmdb_data']
        year = tmdb.get('release_date', tmdb.get('first_air_date', ''))
    
    # Extract year from date string if needed
    if year and '-' in str(year):
        year = str(year).split('-')[0]
    
    if year:
        badges_html += f'<span class="meta-badge year-badge">{year}</span>'
    
    # Rating badge (green with star) - check multiple sources
    rating = None
    
    # Direct rating fields
    rating = item_data.get('rating', item_data.get('vote_average', ''))
    
    # Check TMDB data if available
    if not rating and 'tmdb_data' in item_data:
        tmdb = item_data['tmdb_data']
        rating = tmdb.get('vote_average', '')
    
    # Check if rating is in nested structures
    if not rating and 'ProviderIds' in item_data:
        # This suggests we have Jellyfin data, rating might be elsewhere
        pass
    
    if rating:
        try:
            rating_float = float(rating)
            if rating_float > 0:
                badges_html += f'<span class="meta-badge rating-badge">★ {rating_float:.1f}</span>'
        except (ValueError, TypeError):
            pass
    
    # Source badge (purple)
    source = item_data.get('source', item_data.get('metadata_source', ''))
    
    # Check if we have TMDB data
    if not source and 'tmdb_data' in item_data:
        source = 'TMDB Enhanced'
    elif not source and 'ProviderIds' in item_data:
        provider_ids = item_data['ProviderIds']
        if 'Tmdb' in provider_ids or 'TheMovieDb' in provider_ids:
            source = 'TMDB Enhanced'
    
    if source:
        badges_html += f'<span class="meta-badge source-badge">{source}</span>'
    
    return badges_html


def get_tv_season_info(serie_data: Dict[str, Any]) -> str:
    """Generate season information for TV shows like 'Seasons 4 available • 89 episodes'"""
    seasons = serie_data.get('seasons', {})
    if not seasons:
        return ""
    
    # Count total episodes across all seasons
    total_episodes = 0
    for season_episodes in seasons.values():
        if isinstance(season_episodes, list):
            total_episodes += len(season_episodes)
        elif isinstance(season_episodes, int):
            total_episodes += season_episodes
        elif isinstance(season_episodes, dict):
            # If it's a dict, try to get episode count
            total_episodes += len(season_episodes.get('episodes', []))
    
    season_count = len(seasons)
    
    # Format like "Seasons 4 available • 89 episodes"
    season_text = f"Season{'s' if season_count != 1 else ''} {season_count} available"
    if total_episodes > 0:
        season_text += f" • {total_episodes} episode{'s' if total_episodes != 1 else ''}"
    
    total_text = f"The show has {season_count} season{'s' if season_count != 1 else ''}"
    if total_episodes > 0:
        total_text += f" with {total_episodes} episode{'s' if total_episodes != 1 else ''} in total."
    else:
        total_text += "."
    
    return f"""
    <div class="tv-season-info">
        <div class="season-summary">{season_text}</div>
        <div class="season-total">{total_text}</div>
    </div>
    """


def populate_email_template(movies, series, total_tv, total_movie, config) -> str:
    """
    Enhanced function with metadata badges and improved styling like the photo
    """
    try:
        # Read the template file
        template_path = "/app/templates/email.html"
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template = template_file.read()

        logger.info(f"Template loaded from: {template_path}")

        # Get language from config
        language = getattr(config.email_template, 'language', 'en')

        # Apply translations
        if language in ["fr", "en"]:
            for key in translation[language]:
                template = re.sub(
                    r"\${" + key + "}",
                    translation[language][key],
                    template
                )
        else:
            raise Exception(f"[FATAL] Language {language} not supported. Supported languages are fr and en")

        # Apply custom configuration keys
        custom_keys = [
            {"key": "title", "value": config.email_template.title},
            {"key": "subtitle", "value": config.email_template.subtitle},
            {"key": "emby_url", "value": config.email_template.emby_url},
            {"key": "emby_owner_name", "value": config.email_template.emby_owner_name},
            {"key": "unsubscribe_email", "value": config.email_template.unsubscribe_email}
        ]

        for key in custom_keys:
            template = re.sub(r"\${" + key["key"] + "}", key["value"], template)

        # Movies section with enhanced styling
        if movies:
            template = re.sub(r"\${display_movies}", "", template)
            movies_html = ""

            for movie_title, movie_data in movies.items():
                metadata_badges = get_metadata_badges(movie_data)
                
                # Escape HTML in movie title and description
                safe_title = html.escape(movie_title)
                safe_description = html.escape(movie_data.get('description', ''))
                
                movies_html += f"""
                <div class="movie_container" style="margin-bottom: 15px;">
                    <div class="movie_bg" style="background: url('{movie_data['poster']}') no-repeat center center; background-size: cover; border-radius: 10px;">
                        <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0" style="background: rgba(0, 0, 0, 0.8); border-radius: 10px; width: 100%;">
                            <tr>
                                <td class="movie-image" valign="top" style="padding: 15px; text-align: center; width: 120px;">
                                    <img src="{movie_data['poster']}" alt="{safe_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto; border-radius: 8px;">
                                </td>
                                <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                    <div class="mobile-text-container">
                                        <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 8px !important; font-size: 18px !important; font-weight: 600;">{safe_title}</h3>
                                        <div style="margin-bottom: 12px;">
                                            {metadata_badges}
                                        </div>
                                        <div class="movie-description" style="color: #ffffff !important; font-size: 14px !important; line-height: 1.5 !important;">
                                            {safe_description}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
                """

            template = re.sub(r"\${films}", movies_html, template)
        else:
            template = re.sub(r"\${display_movies}", "display:none", template)

        # TV Shows section with enhanced styling and season info
        if series:
            template = re.sub(r"\${display_tv}", "", template)
            series_html = ""

            for serie_title, serie_data in series.items():
                metadata_badges = get_metadata_badges(serie_data)
                season_info = get_tv_season_info(serie_data)
                
                # Escape HTML in series title and description
                safe_title = html.escape(serie_title)
                safe_description = html.escape(serie_data.get('description', ''))
                
                series_html += f"""
                <div class="movie_container" style="margin-bottom: 15px;">
                    <div class="movie_bg" style="background: url('{serie_data['poster']}') no-repeat center center; background-size: cover; border-radius: 10px;">
                        <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0" style="background: rgba(0, 0, 0, 0.8); border-radius: 10px; width: 100%;">
                            <tr>
                                <td class="movie-image" valign="top" style="padding: 15px; text-align: center; width: 120px;">
                                    <img src="{serie_data['poster']}" alt="{safe_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto; border-radius: 8px;">
                                </td>
                                <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                    <div class="mobile-text-container">
                                        <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 8px !important; font-size: 18px !important; font-weight: 600;">{safe_title}</h3>
                                        <div style="margin-bottom: 12px;">
                                            {metadata_badges}
                                        </div>
                                        <div class="movie-description" style="color: #ffffff !important; font-size: 14px !important; line-height: 1.5 !important;">
                                            {safe_description}
                                        </div>
                                        {season_info}
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
                """

            template = re.sub(r"\${tvs}", series_html, template)
        else:
            template = re.sub(r"\${display_tv}", "display:none", template)

        # Statistics section
        template = re.sub(r"\${series_count}", str(total_tv), template)
        template = re.sub(r"\${movies_count}", str(total_movie), template)

        logger.info(f"Template populated successfully with enhanced styling: {total_movie} movies, {total_tv} episodes")
        return template

    except Exception as e:
        logger.error(f"Error populating email template: {e}")
        raise


def render_email_with_server_stats(context: Dict[str, Any], config_path: str = "config.yml") -> str:
    """
    Main function to render email with enhanced metadata
    """
    try:
        # Convert context to the format expected by populate_email_template
        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        # Convert movies list to dictionary format with enhanced data
        movies_dict = {}
        for movie in movies:
            title = movie.get('title', 'Unknown')
            
            # Pass the full movie data to preserve API structures
            movies_dict[title] = {
                'created_on': movie.get('date_added', ''),
                'description': movie.get('overview', ''),
                'poster': movie.get('poster_url', ''),
                # Keep all the original data for metadata extraction
                **movie  # This preserves ProviderIds, tmdb_data, etc.
            }

        # Convert TV shows list to dictionary format with enhanced data  
        series_dict = {}
        for show in tv_shows:
            title = show.get('title', 'Unknown')
            seasons = show.get('seasons', {})

            # Pass the full show data to preserve API structures
            series_dict[title] = {
                'created_on': show.get('date_added', ''),
                'description': show.get('overview', ''),
                'poster': show.get('poster_url', ''),
                'seasons': seasons,
                # Keep all the original data for metadata extraction
                **show  # This preserves ProviderIds, tmdb_data, etc.
            }

        # Get the total server statistics
        total_movies_server = context.get('total_movies_server', 0)
        total_episodes_server = context.get('total_episodes_server', 0)

        # Debug logging
        logger.info(f"Context total_movies_server: {total_movies_server}")
        logger.info(f"Context total_episodes_server: {total_episodes_server}")

        # If we don't have server totals, try alternative keys
        if total_movies_server == 0 or total_episodes_server == 0:
            logger.warning("Server totals not provided in context, trying to fetch...")

            total_movies_server = context.get('total_movies_on_server',
                                              context.get('server_movie_count',
                                                          context.get('movie_count_total', 0)))
            total_episodes_server = context.get('total_episodes_on_server',
                                                context.get('server_episode_count',
                                                            context.get('episode_count_total', 0)))

        logger.info(f"Final server totals: Movies={total_movies_server}, Episodes={total_episodes_server}")

        # Create mock config object
        class MockConfig:
            def __init__(self, context):
                self.email_template = type('obj', (object,), {
                    'language': context.get('language', 'en'),
                    'title': context.get('title', 'Emby Newsletter'),
                    'subtitle': context.get('subtitle', ''),
                    'emby_url': context.get('emby_url', ''),
                    'emby_owner_name': context.get('emby_owner_name', ''),
                    'unsubscribe_email': context.get('unsubscribe_email', '')
                })

        config = MockConfig(context)

        return populate_email_template(movies_dict, series_dict, total_episodes_server, total_movies_server, config)

    except Exception as e:
        logger.error(f"Error rendering email with server stats: {e}")
        raise


# Keep existing functions for compatibility
def load_config(config_path: str = "config.yml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return config or {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def get_emby_server_statistics(emby_url: str, api_key: str) -> Dict[str, int]:
    """Fetch total server statistics from Emby API."""
    try:
        import requests

        emby_url = emby_url.rstrip('/')
        headers = {'X-Emby-Token': api_key}

        api_endpoints = [
            f"{emby_url}/emby/Items",
            f"{emby_url}/Items",
            f"{emby_url}/api/Items"
        ]

        total_movies = 0
        total_episodes = 0

        for endpoint in api_endpoints:
            try:
                logger.debug(f"Trying endpoint: {endpoint}")

                movies_response = requests.get(
                    endpoint,
                    params={
                        'IncludeItemTypes': 'Movie',
                        'Recursive': 'true',
                        'Fields': 'ItemCounts'
                    },
                    headers=headers,
                    timeout=10
                )

                episodes_response = requests.get(
                    endpoint,
                    params={
                        'IncludeItemTypes': 'Episode',
                        'Recursive': 'true',
                        'Fields': 'ItemCounts'
                    },
                    headers=headers,
                    timeout=10
                )

                if movies_response.status_code == 200 and episodes_response.status_code == 200:
                    total_movies = movies_response.json().get('TotalRecordCount', 0)
                    total_episodes = episodes_response.json().get('TotalRecordCount', 0)
                    logger.info(f"Success with endpoint: {endpoint}")
                    logger.debug(f"Retrieved {total_movies} movies and {total_episodes} episodes from server")

                    return {
                        'total_movies_server': total_movies,
                        'total_episodes_server': total_episodes
                    }
                else:
                    logger.debug(
                        f"Failed with endpoint {endpoint}: movies={movies_response.status_code}, episodes={episodes_response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for endpoint {endpoint}: {e}")
                continue

        logger.warning("All API endpoints failed or returned zero results")
        return {'total_movies_server': 0, 'total_episodes_server': 0}

    except ImportError:
        logger.error("requests library not available for API calls")
        return {'total_movies_server': 0, 'total_episodes_server': 0}
    except Exception as e:
        logger.error(f"Error fetching server statistics: {e}")
        return {'total_movies_server': 0, 'total_episodes_server': 0}


# Example usage and data format helper
def example_usage():
    """
    Example of how to use the enhanced template renderer
    """
    # Example context data with metadata
    sample_context = {
        'language': 'en',
        'title': 'Weekly Emby Newsletter',
        'subtitle': 'New content this week',
        'emby_url': 'https://emby.example.com',
        'emby_owner_name': 'John Doe',
        'unsubscribe_email': 'unsubscribe@example.com',
        'total_movies_server': 1247,
        'total_episodes_server': 8934,
        'movies': [
            {
                'title': 'The Karate Kid',
                'date_added': '2024-01-15T10:30:00Z',
                'overview': '12-year-old Dre Parker could\'ve been the most popular kid in Detroit...',
                'poster_url': 'https://image.tmdb.org/path/to/poster.jpg',
                'year': '2010',
                'tmdb_rating': '6.6',
                'metadata_source': 'TMDB Enhanced'
            }
        ],
        'tv_shows': [
            {
                'title': 'Once Upon a Time',
                'date_added': '2024-01-14T15:45:00Z',
                'overview': 'There is a town in Maine where every story book character...',
                'poster_url': 'https://image.tmdb.org/path/to/poster2.jpg',
                'year': '2011',
                'tmdb_rating': '7.4',
                'metadata_source': 'TMDB Enhanced',
                'seasons': {
                    'Season 1': 22,  # 22 episodes
                    'Season 2': 22,
                    'Season 3': 22,
                    'Season 4': 23
                }
            }
        ]
    }
    
    # Render the email
    html_output = render_email_with_server_stats(sample_context)
    return html_output


if __name__ == "__main__":
    # Test the enhanced template
    print("Testing enhanced template renderer...")
    try:
        html = example_usage()
        print("✅ Template rendered successfully!")
        print(f"Output length: {len(html)} characters")
    except Exception as e:
        print(f"❌ Error: {e}")