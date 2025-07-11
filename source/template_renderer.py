#!/usr/bin/env python3
"""
Template rendering for Emby Newsletter using the original approach
Based on the original email_template.py implementation
"""

import os
import logging
import html
import re
import yaml
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Translation dictionary like the original
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
    Generate newsletter content using template file (like original implementation)
    """
    try:
        # Read the template file
        template_path = "/app/templates/email.html"
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template = template_file.read()

        logger.info(f"Template loaded from: {template_path}")

        # Get language from config
        language = getattr(config.email_template, 'language', 'en')

        # Apply translations like the original
        if language in ["fr", "en"]:
            for key in translation[language]:
                template = re.sub(
                    r"\${" + key + "}",
                    translation[language][key],
                    template
                )
        else:
            raise Exception(f"[FATAL] Language {language} not supported. Supported languages are fr and en")

        # Apply custom configuration keys like the original
        custom_keys = [
            {"key": "title", "value": config.email_template.title},
            {"key": "subtitle", "value": config.email_template.subtitle},
            {"key": "emby_url", "value": config.email_template.emby_url},
            {"key": "emby_owner_name", "value": config.email_template.emby_owner_name},
            {"key": "unsubscribe_email", "value": config.email_template.unsubscribe_email}
        ]

        for key in custom_keys:
            template = re.sub(r"\${" + key["key"] + "}", key["value"], template)

        # Calculate statistics for the 4-column layout
        total_content_server = total_movie + total_tv
        new_movies_count = len(movies) if movies else 0
        new_tv_count = len(series) if series else 0
        new_content_total = new_movies_count + new_tv_count

        # Statistics replacements for the new layout
        stats_replacements = {
            "total_content": str(total_content_server),
            "movies_count": str(total_movie),
            "series_count": str(total_tv),
            "new_content": str(new_content_total)
        }

        for key, value in stats_replacements.items():
            template = re.sub(r"\${" + key + "}", value, template)

        # Movies section (like the original)
        if movies:
            template = re.sub(r"\${display_movies}", "", template)
            movies_html = ""

            for movie_title, movie_data in movies.items():
                added_date = movie_data.get("created_on", "").split("T")[0] if movie_data.get("created_on") else ""

                # Build enhanced movie HTML with TMDB data
                meta_html = ""
                if movie_data.get("year"):
                    meta_html += f'<span style="background: rgba(239, 68, 68, 0.15); color: #fca5a5; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 8px; border: 1px solid rgba(239, 68, 68, 0.3);">{movie_data["year"]}</span>'

                # Add TMDB rating if available
                if movie_data.get("tmdb_data") and movie_data["tmdb_data"].get("vote_average"):
                    rating = movie_data["tmdb_data"]["vote_average"]
                    if rating > 0:
                        meta_html += f'<span style="background: rgba(34, 197, 94, 0.15); color: #86efac; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 8px; border: 1px solid rgba(34, 197, 94, 0.3);">★ {rating:.1f}</span>'

                # Add source indicator
                if movie_data.get("tmdb_data"):
                    meta_html += '<span style="background: rgba(168, 85, 247, 0.15); color: #c4b5fd; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 500; border: 1px solid rgba(168, 85, 247, 0.3);">TMDB Enhanced</span>'
                else:
                    meta_html += '<span style="background: rgba(168, 85, 247, 0.15); color: #c4b5fd; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 500; border: 1px solid rgba(168, 85, 247, 0.3);">Emby</span>'

                # Use TMDB description if available, otherwise Emby
                description = ""
                if movie_data.get("tmdb_data") and movie_data["tmdb_data"].get("overview"):
                    description = movie_data["tmdb_data"]["overview"]
                else:
                    description = movie_data.get("description", "")

                # Use TMDB poster if available, otherwise Emby
                poster_url = ""
                if movie_data.get("tmdb_data") and movie_data["tmdb_data"].get("poster_path"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{movie_data['tmdb_data']['poster_path']}"
                else:
                    poster_url = movie_data.get("poster",
                                                "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png")

                movies_html += f"""
                <div class="movie_container" style="margin-bottom: 15px;">
                    <div class="movie_bg" style="background: url('{poster_url}') no-repeat center center; background-size: cover; border-radius: 10px;">
                        <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0" style="background: rgba(0, 0, 0, 0.7); border-radius: 10px; width: 100%;">
                            <tr>
                                <td class="movie-image" valign="top" style="padding: 15px; text-align: center; width: 120px;">
                                    <img src="{poster_url}" alt="{movie_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto;">
                                </td>
                                <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                    <div class="mobile-text-container">
                                        <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 5px !important; font-size: 18px !important;">{movie_title}</h3>
                                        <div class="movie-date" style="color: #dddddd !important; font-size: 14px !important; margin: 0 0 10px !important;">
                                            {meta_html}
                                        </div>
                                        <div class="movie-description" style="color: #dddddd !important; font-size: 14px !important; line-height: 1.4 !important;">
                                            {description}
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

        # TV Shows section (like the original but enhanced)
        if series:
            template = re.sub(r"\${display_tv}", "", template)
            series_html = ""

            for serie_title, serie_data in series.items():
                added_date = serie_data.get("created_on", "").split("T")[0] if serie_data.get("created_on") else ""

                # Build enhanced TV show HTML with TMDB data
                meta_html = ""
                if serie_data.get("year"):
                    meta_html += f'<span style="background: rgba(239, 68, 68, 0.15); color: #fca5a5; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 8px; border: 1px solid rgba(239, 68, 68, 0.3);">{serie_data["year"]}</span>'

                # Add TMDB rating if available
                if serie_data.get("tmdb_data") and serie_data["tmdb_data"].get("vote_average"):
                    rating = serie_data["tmdb_data"]["vote_average"]
                    if rating > 0:
                        meta_html += f'<span style="background: rgba(34, 197, 94, 0.15); color: #86efac; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 8px; border: 1px solid rgba(34, 197, 94, 0.3);">★ {rating:.1f}</span>'

                # Add source indicator
                if serie_data.get("tmdb_data"):
                    meta_html += '<span style="background: rgba(168, 85, 247, 0.15); color: #c4b5fd; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 500; border: 1px solid rgba(168, 85, 247, 0.3);">TMDB Enhanced</span>'
                else:
                    meta_html += '<span style="background: rgba(168, 85, 247, 0.15); color: #c4b5fd; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 500; border: 1px solid rgba(168, 85, 247, 0.3);">Emby</span>'

                # Use TMDB description if available, otherwise Emby
                description = ""
                if serie_data.get("tmdb_data") and serie_data["tmdb_data"].get("overview"):
                    description = serie_data["tmdb_data"]["overview"]
                else:
                    description = serie_data.get("description", "")

                # Use TMDB poster if available, otherwise Emby
                poster_url = ""
                if serie_data.get("tmdb_data") and serie_data["tmdb_data"].get("poster_path"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{serie_data['tmdb_data']['poster_path']}"
                else:
                    poster_url = serie_data.get("poster",
                                                "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png")

                # Build seasons info with compact format
                seasons_info = ""
                seasons = serie_data.get("seasons", [])
                if seasons:
                    if len(seasons) == 1:
                        season_num = seasons[0].replace("Season ", "").replace("season ", "")
                        total_episodes = serie_data.get("total_episodes", "?")
                        seasons_info = f"""
                        <div class="tv-season-info">
                            <div class="season-summary">Season {season_num} • {total_episodes} episodes</div>
                            <div class="season-total">The show has {season_num} season with {total_episodes} episodes in total.</div>
                        </div>"""
                    else:
                        seasons_str = ", ".join(seasons)
                        total_episodes = serie_data.get("total_episodes", len(seasons))

                        # Get total from TMDB if available
                        total_seasons_tmdb = serie_data.get("tmdb_data", {}).get("number_of_seasons", len(seasons))
                        total_episodes_tmdb = serie_data.get("tmdb_data", {}).get("number_of_episodes", total_episodes)

                        seasons_info = f"""
                        <div class="tv-season-info">
                            <div class="season-summary">Seasons {len(seasons)} available • {total_episodes} episodes</div>
                            <div class="season-total">The show has {total_seasons_tmdb} seasons with {total_episodes_tmdb} episodes in total.</div>
                        </div>"""

                series_html += f"""
                <div class="movie_container" style="margin-bottom: 15px;">
                    <div class="movie_bg" style="background: url('{poster_url}') no-repeat center center; background-size: cover; border-radius: 10px;">
                        <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0" style="background: rgba(0, 0, 0, 0.7); border-radius: 10px; width: 100%;">
                            <tr>
                                <td class="movie-image" valign="top" style="padding: 15px; text-align: center; width: 120px;">
                                    <img src="{poster_url}" alt="{serie_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto;">
                                </td>
                                <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                    <div class="mobile-text-container">
                                        <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 5px !important; font-size: 18px !important;">{serie_title}</h3>
                                        <div class="movie-date" style="color: #dddddd !important; font-size: 14px !important; margin: 0 0 10px !important;">
                                            {meta_html}
                                        </div>
                                        <div class="movie-description" style="color: #dddddd !important; font-size: 14px !important; line-height: 1.4 !important;">
                                            {description}
                                        </div>
                                        {seasons_info}
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

        logger.info("Template populated successfully")
        return template

    except Exception as e:
        logger.error(f"Error populating email template: {e}")
        raise


def render_email_with_server_stats(context: Dict[str, Any], config_path: str = "config.yml") -> str:
    """
    Main function to render email (replacement for the complex previous version)
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
                'year': movie.get('year'),
                'created_on': movie.get('date_added'),
                'description': movie.get('overview', ''),
                'poster': movie.get('poster_url', ''),
                'tmdb_data': movie.get('tmdb_data')
            }

        # Convert TV shows list to dictionary format like original
        series_dict = {}
        for show in tv_shows:
            title = show.get('title', 'Unknown')
            seasons = show.get('seasons', {})

            # Calculate total episodes
            total_episodes = sum(len(episodes) for episodes in seasons.values() if isinstance(episodes, list))

            series_dict[title] = {
                'year': show.get('year'),
                'created_on': show.get('date_added'),
                'description': show.get('overview', ''),
                'poster': show.get('poster_url', ''),
                'seasons': list(seasons.keys()) if seasons else [],
                'total_episodes': total_episodes,
                'tmdb_data': show.get('tmdb_data')
            }

        # Get totals
        total_movies = context.get('total_movies_server', len(movies))
        total_tv_shows = context.get('total_tv_shows_server', len(tv_shows))

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

        return populate_email_template(movies_dict, series_dict, total_tv_shows, total_movies, config)

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
        total_series = 0

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

                # Get total TV shows
                series_response = requests.get(
                    endpoint,
                    params={
                        'IncludeItemTypes': 'Series',
                        'Recursive': 'true',
                        'Fields': 'ItemCounts'
                    },
                    headers=headers,
                    timeout=10
                )

                if movies_response.status_code == 200 and series_response.status_code == 200:
                    total_movies = movies_response.json().get('TotalRecordCount', 0)
                    total_series = series_response.json().get('TotalRecordCount', 0)
                    logger.info(f"Success with endpoint: {endpoint}")
                    logger.debug(f"Retrieved {total_movies} movies and {total_series} TV shows from server")
                    break
                else:
                    logger.debug(
                        f"Failed with endpoint {endpoint}: movies={movies_response.status_code}, series={series_response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for endpoint {endpoint}: {e}")
                continue

        if total_movies == 0 and total_series == 0:
            logger.warning("All API endpoints failed or returned zero results")

        return {
            'total_movies_server': total_movies,
            'total_tv_shows_server': total_series
        }

    except ImportError:
        logger.error("requests library not available for API calls")
        return {'total_movies_server': 0, 'total_tv_shows_server': 0}
    except Exception as e:
        logger.error(f"Error fetching server statistics: {e}")
        return {'total_movies_server': 0, 'total_tv_shows_server': 0}