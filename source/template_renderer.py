#!/usr/bin/env python3
"""
Enhanced Template rendering for Emby Newsletter
Combines the simplicity of original email_template.py with enhanced features
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


def create_metadata_badges(movie_data: Dict[str, Any]) -> str:
    """Create metadata badges for movies/shows with enhanced styling"""
    meta_html = ""

    # Year badge
    if movie_data.get("year"):
        meta_html += f'<span class="meta-badge year-badge">{movie_data["year"]}</span>'

    # TMDB rating badge
    if movie_data.get("tmdb_data") and movie_data["tmdb_data"].get("vote_average"):
        rating = movie_data["tmdb_data"]["vote_average"]
        if rating > 0:
            meta_html += f'<span class="meta-badge rating-badge">★ {rating:.1f}</span>'

    # Source indicator badge
    if movie_data.get("tmdb_data"):
        meta_html += '<span class="meta-badge source-badge">TMDB Enhanced</span>'
    else:
        meta_html += '<span class="meta-badge source-badge">Emby</span>'

    return meta_html


def create_movie_card(title: str, movie_data: Dict[str, Any], language: str) -> str:
    """Create a single movie card HTML - simplified approach like original"""

    # Get the added date
    added_date = movie_data.get("created_on", "").split("T")[0] if movie_data.get("created_on") else ""

    # Create metadata badges
    meta_html = create_metadata_badges(movie_data)

    # Use TMDB description if available, otherwise Emby
    description = ""
    if movie_data.get("tmdb_data") and movie_data["tmdb_data"].get("overview"):
        description = html.escape(
            movie_data["tmdb_data"]["overview"][:300] + "..." if len(movie_data["tmdb_data"]["overview"]) > 300 else
            movie_data["tmdb_data"]["overview"])
    else:
        description = html.escape(movie_data.get("description", "")[:300] + "..." if len(
            movie_data.get("description", "")) > 300 else movie_data.get("description", ""))

    # Use TMDB poster if available, otherwise Emby
    poster_url = ""
    if movie_data.get("tmdb_data") and movie_data["tmdb_data"].get("poster_path"):
        poster_url = f"https://image.tmdb.org/t/p/w500{movie_data['tmdb_data']['poster_path']}"
    else:
        poster_url = movie_data.get("poster",
                                    "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png")

    # Escape the title
    safe_title = html.escape(title)

    # Simple card structure like original but with background image
    return f"""
    <div class="movie_container" style="margin-bottom: 15px;">
        <div class="movie_bg" style="background: url('{poster_url}') no-repeat center center; background-size: cover; border-radius: 10px;">
            <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td class="movie-image">
                        <img src="{poster_url}" alt="{safe_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto; border-radius: 8px;">
                    </td>
                    <td class="movie-content-cell">
                        <div class="mobile-text-container">
                            <h3 class="movie-title">{safe_title}</h3>
                            <div class="movie-date">
                                {meta_html}
                            </div>
                            <div class="movie-description">
                                {description}
                            </div>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
    </div>
    """


def create_tv_show_card(title: str, serie_data: Dict[str, Any], language: str) -> str:
    """Create a single TV show card HTML with season information"""

    # Get the added date
    added_date = serie_data.get("created_on", "").split("T")[0] if serie_data.get("created_on") else ""

    # Create metadata badges
    meta_html = create_metadata_badges(serie_data)

    # Use TMDB description if available, otherwise Emby
    description = ""
    if serie_data.get("tmdb_data") and serie_data["tmdb_data"].get("overview"):
        description = html.escape(
            serie_data["tmdb_data"]["overview"][:300] + "..." if len(serie_data["tmdb_data"]["overview"]) > 300 else
            serie_data["tmdb_data"]["overview"])
    else:
        description = html.escape(serie_data.get("description", "")[:300] + "..." if len(
            serie_data.get("description", "")) > 300 else serie_data.get("description", ""))

    # Use TMDB poster if available, otherwise Emby
    poster_url = ""
    if serie_data.get("tmdb_data") and serie_data["tmdb_data"].get("poster_path"):
        poster_url = f"https://image.tmdb.org/t/p/w500{serie_data['tmdb_data']['poster_path']}"
    else:
        poster_url = serie_data.get("poster",
                                    "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png")

    # Escape the title
    safe_title = html.escape(title)

    # Build seasons info with compact format
    seasons_info = ""
    seasons = serie_data.get("seasons", [])
    total_episodes = serie_data.get("total_episodes", 0)

    if seasons:
        if len(seasons) == 1:
            season_num = seasons[0].replace("Season ", "").replace("season ", "")
            seasons_info = f"""
            <div class="tv-season-info">
                <div class="season-summary">Season {season_num} • {total_episodes} episodes</div>
                <div class="season-total">The show has {season_num} season with {total_episodes} episodes in total.</div>
            </div>"""
        else:
            # Get total from TMDB if available
            total_seasons_tmdb = serie_data.get("tmdb_data", {}).get("number_of_seasons", len(seasons))
            total_episodes_tmdb = serie_data.get("tmdb_data", {}).get("number_of_episodes", total_episodes)

            seasons_info = f"""
            <div class="tv-season-info">
                <div class="season-summary">{len(seasons)} seasons available • {total_episodes} episodes</div>
                <div class="season-total">The show has {total_seasons_tmdb} seasons with {total_episodes_tmdb} episodes in total.</div>
            </div>"""

    return f"""
    <div class="movie_container" style="margin-bottom: 15px;">
        <div class="movie_bg" style="background: url('{poster_url}') no-repeat center center; background-size: cover; border-radius: 10px;">
            <table class="movie" width="100%" role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td class="movie-image">
                        <img src="{poster_url}" alt="{safe_title}" style="max-width: 100px; height: auto; display: block; margin: 0 auto; border-radius: 8px;">
                    </td>
                    <td class="movie-content-cell">
                        <div class="mobile-text-container">
                            <h3 class="movie-title">{safe_title}</h3>
                            <div class="movie-date">
                                {meta_html}
                            </div>
                            <div class="movie-description">
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


def populate_email_template(movies, series, total_tv, total_movie, config) -> str:
    """
    Generate newsletter content using template file (simplified approach like original)
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

        # Movies section - simplified like original but enhanced
        if movies:
            template = re.sub(r"\${display_movies}", "", template)
            movies_html = ""

            for movie_title, movie_data in movies.items():
                movies_html += create_movie_card(movie_title, movie_data, language)

            template = re.sub(r"\${films}", movies_html, template)
        else:
            template = re.sub(r"\${display_movies}", "display:none", template)

        # TV Shows section - simplified like original but enhanced
        if series:
            template = re.sub(r"\${display_tv}", "", template)
            series_html = ""

            for serie_title, serie_data in series.items():
                series_html += create_tv_show_card(serie_title, serie_data, language)

            template = re.sub(r"\${tvs}", series_html, template)
        else:
            template = re.sub(r"\${display_tv}", "display:none", template)

        # Statistics section (like the original) - USE TOTAL SERVER COUNTS!
        template = re.sub(r"\${series_count}", str(total_tv), template)
        template = re.sub(r"\${movies_count}", str(total_movie), template)

        logger.info("Template populated successfully")
        return template

    except Exception as e:
        logger.error(f"Error populating email template: {e}")
        raise


def render_email_with_server_stats(context: Dict[str, Any], config_path: str = "config.yml") -> str:
    """
    Main function to render email - FIXED to use server totals
    """
    try:
        # Convert context to the format expected by populate_email_template
        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        # Try to get server statistics if not already in context
        if 'total_movies_server' not in context or 'total_tv_shows_server' not in context:
            emby_url = context.get('emby_url', '')
            api_key = context.get('api_key', '')

            if emby_url and api_key:
                server_stats = get_emby_server_statistics(emby_url, api_key)
                context.update(server_stats)
                logger.info(f"Fetched server stats: {server_stats}")

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

        # FIXED: Get TOTAL SERVER COUNTS, not just new items!
        # This is the key fix - we prioritize server totals over new content counts
        total_movies_server = context.get('total_movies_server', 0)
        total_tv_shows_server = context.get('total_tv_shows_server', 0)

        # Only fall back to new items count if server totals are 0 or missing
        if total_movies_server == 0:
            total_movies_server = len(movies)
            logger.warning(f"Server movie count was 0, using new movies count: {total_movies_server}")

        if total_tv_shows_server == 0:
            total_tv_shows_server = len(tv_shows)
            logger.warning(f"Server TV count was 0, using new TV shows count: {total_tv_shows_server}")

        logger.info(f"Using server totals - Movies: {total_movies_server}, TV Shows: {total_tv_shows_server}")

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

        # Pass the TOTAL SERVER COUNTS to the template function
        return populate_email_template(movies_dict, series_dict, total_tv_shows_server, total_movies_server, config)

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

                # Get total TV shows (Episodes, not Series for episode count)
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
                        'total_tv_shows_server': total_episodes  # Episodes count, not series count
                    }
                else:
                    logger.debug(
                        f"Failed with endpoint {endpoint}: movies={movies_response.status_code}, episodes={episodes_response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for endpoint {endpoint}: {e}")
                continue

        logger.warning("All API endpoints failed or returned zero results")
        return {'total_movies_server': 0, 'total_tv_shows_server': 0}

    except ImportError:
        logger.error("requests library not available for API calls")
        return {'total_movies_server': 0, 'total_tv_shows_server': 0}
    except Exception as e:
        logger.error(f"Error fetching server statistics: {e}")
        return {'total_movies_server': 0, 'total_tv_shows_server': 0}