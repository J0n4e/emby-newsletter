#!/usr/bin/env python3
"""
Template rendering for Emby Newsletter using the EXACT original approach
Based on the original email_template.py implementation
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


def populate_email_template(movies, series, total_tv, total_movie, config) -> str:
    """
    EXACT same function as original email_template.py but with enhanced HTML template
    """
    try:
        # Read the template file
        template_path = "/app/templates/email.html"
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template = template_file.read()

        logger.info(f"Template loaded from: {template_path}")

        # Get language from config - EXACT same as original
        language = getattr(config.email_template, 'language', 'en')

        # Apply translations - EXACT same as original
        if language in ["fr", "en"]:
            for key in translation[language]:
                template = re.sub(
                    r"\${" + key + "}",
                    translation[language][key],
                    template
                )
        else:
            raise Exception(f"[FATAL] Language {language} not supported. Supported languages are fr and en")

        # Apply custom configuration keys - EXACT same as original
        custom_keys = [
            {"key": "title", "value": config.email_template.title},
            {"key": "subtitle", "value": config.email_template.subtitle},
            {"key": "emby_url", "value": config.email_template.emby_url},
            {"key": "emby_owner_name", "value": config.email_template.emby_owner_name},
            {"key": "unsubscribe_email", "value": config.email_template.unsubscribe_email}
        ]

        for key in custom_keys:
            template = re.sub(r"\${" + key["key"] + "}", key["value"], template)

        # Movies section - EXACT same logic as original
        if movies:
            template = re.sub(r"\${display_movies}", "", template)
            movies_html = ""

            for movie_title, movie_data in movies.items():
                added_date = movie_data["created_on"].split("T")[0]
                movies_html += f"""
                <div class="movie_container" style="margin-bottom: 15px;">
                    <div class="movie_bg" style="background: url('{movie_data['poster']}') no-repeat center center; background-size: cover; border-radius: 10px;">
                        <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0" style="background: rgba(0, 0, 0, 0.7); border-radius: 10px; width: 100%;">
                            <tr>
                                <td class="movie-image" valign="top" style="padding: 15px; text-align: center; width: 120px;">
                                    <img src="{movie_data['poster']}" alt="{movie_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto;">
                                </td>
                                <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                    <div class="mobile-text-container">
                                        <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 5px !important; font-size: 18px !important;">{movie_title}</h3>
                                        <div class="movie-date" style="color: #dddddd !important; font-size: 14px !important; margin: 0 0 10px !important;">
                                            {translation[language]['added_on']} {added_date}
                                        </div>
                                        <div class="movie-description" style="color: #dddddd !important; font-size: 14px !important; line-height: 1.4 !important;">
                                            {movie_data['description']}
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

        # TV Shows section - EXACT same logic as original
        if series:
            template = re.sub(r"\${display_tv}", "", template)
            series_html = ""

            for serie_title, serie_data in series.items():
                added_date = serie_data["created_on"].split("T")[0]
                seasons_str = ", ".join(serie_data["seasons"])
                series_html += f"""
                <div class="movie_container" style="margin-bottom: 15px;">
                    <div class="movie_bg" style="background: url('{serie_data['poster']}') no-repeat center center; background-size: cover; border-radius: 10px;">
                        <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0" style="background: rgba(0, 0, 0, 0.7); border-radius: 10px; width: 100%;">
                            <tr>
                                <td class="movie-image" valign="top" style="padding: 15px; text-align: center; width: 120px;">
                                    <img src="{serie_data['poster']}" alt="{serie_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto;">
                                </td>
                                <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                    <div class="mobile-text-container">
                                        <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 5px !important; font-size: 18px !important;">{serie_title} {seasons_str}</h3>
                                        <div class="movie-date" style="color: #dddddd !important; font-size: 14px !important; margin: 0 0 10px !important;">
                                            {translation[language]['added_on']} {added_date}
                                        </div>
                                        <div class="movie-description" style="color: #dddddd !important; font-size: 14px !important; line-height: 1.4 !important;">
                                            {serie_data['description']}
                                        </div>
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

        # Statistics section - EXACT same as original
        template = re.sub(r"\${series_count}", str(total_tv), template)
        template = re.sub(r"\${movies_count}", str(total_movie), template)

        logger.info(f"Template populated successfully with stats: {total_movie} movies, {total_tv} episodes")
        return template

    except Exception as e:
        logger.error(f"Error populating email template: {e}")
        raise


def render_email_with_server_stats(context: Dict[str, Any], config_path: str = "config.yml") -> str:
    """
    Main function to render email - expects total_tv and total_movie to be passed correctly
    """
    try:
        # Convert context to the format expected by populate_email_template
        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        # Convert movies list to dictionary format like original
        movies_dict = {}
        for movie in movies:
            title = movie.get('title', 'Unknown')
            movies_dict[title] = {
                'created_on': movie.get('date_added', ''),
                'description': movie.get('overview', ''),
                'poster': movie.get('poster_url', ''),
            }

        # Convert TV shows list to dictionary format like original
        series_dict = {}
        for show in tv_shows:
            title = show.get('title', 'Unknown')
            seasons = show.get('seasons', {})

            series_dict[title] = {
                'created_on': show.get('date_added', ''),
                'description': show.get('overview', ''),
                'poster': show.get('poster_url', ''),
                'seasons': list(seasons.keys()) if seasons else [],
            }

        # THE KEY PART: Get the total server statistics
        # These should be the TOTAL counts from your Emby server, not just new items
        total_movies_server = context.get('total_movies_server', 0)
        total_episodes_server = context.get('total_episodes_server', 0)

        # Debug logging
        logger.info(f"Context total_movies_server: {total_movies_server}")
        logger.info(f"Context total_episodes_server: {total_episodes_server}")

        # If we don't have server totals, we need to fetch them
        if total_movies_server == 0 or total_episodes_server == 0:
            logger.warning("Server totals not provided in context, trying to fetch...")

            # Try to get them from context with different keys
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

        # Call exactly like the original: populate_email_template(movies, series, total_tv, total_movie)
        return populate_email_template(movies_dict, series_dict, total_episodes_server, total_movies_server, config)

    except Exception as e:
        logger.error(f"Error rendering email with server stats: {e}")
        raise


# Keep these functions for compatibility
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

        # Clean up the URL (remove trailing slash if present)
        emby_url = emby_url.rstrip('/')

        headers = {'X-Emby-Token': api_key}

        # Try different API endpoints - Emby/Jellyfin can vary
        api_endpoints = [
            f"{emby_url}/emby/Items",  # Standard Emby
            f"{emby_url}/Items",  # Alternative
            f"{emby_url}/api/Items"  # Another alternative
        ]

        total_movies = 0
        total_episodes = 0

        for endpoint in api_endpoints:
            try:
                logger.debug(f"Trying endpoint: {endpoint}")

                # Get total movies
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

                # Get total episodes
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