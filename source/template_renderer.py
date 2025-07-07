#!/usr/bin/env python3
"""
Secure template rendering for Emby Newsletter using string templates
"""

import os
import logging
import html
import re
from typing import Dict, List, Any
from string import Template

logger = logging.getLogger(__name__)


class SecureTemplateRenderer:
    """Secure template renderer with XSS protection using string templates"""

    def __init__(self, template_dir: str = "/app/templates"):
        """Initialize the secure template renderer"""
        self.template_dir = template_dir

    def _secure_escape(self, value: Any) -> str:
        """Escape HTML and dangerous content"""
        if value is None:
            return ""

        str_value = str(value)
        escaped = html.escape(str_value, quote=True)

        dangerous_patterns = [
            ('javascript:', 'j_avascript:'),
            ('vbscript:', 'v_bscript:'),
            ('data:', 'd_ata:'),
            ('<script', '&lt;script'),
            ('</script>', '&lt;/script&gt;'),
            ('onclick', 'o_nclick'),
            ('onload', 'o_nload'),
            ('onerror', 'o_nerror'),
        ]

        for pattern, replacement in dangerous_patterns:
            escaped = escaped.replace(pattern.lower(), replacement)
            escaped = escaped.replace(pattern.upper(), replacement.upper())
            escaped = escaped.replace(pattern.capitalize(), replacement.capitalize())

        return escaped

    def render_email_template(self, context: Dict[str, Any]) -> str:
        """Render the email template with secure context"""
        try:
            safe_context = self._sanitize_context(context)
            html_content = self._build_html_email(safe_context)
            logger.debug("Email template rendered successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            safe_context = self._sanitize_context(context)
            return self._build_html_email(safe_context)

    def _build_html_email(self, context: Dict[str, Any]) -> str:
        """Build HTML email using secure string construction"""
        title = self._secure_escape(context.get('title', 'Emby Newsletter'))
        subtitle = self._secure_escape(context.get('subtitle', ''))
        language = self._secure_escape(context.get('language', 'en'))
        emby_url = self._secure_escape(context.get('emby_url', ''))
        emby_owner_name = self._secure_escape(context.get('emby_owner_name', ''))
        unsubscribe_email = self._secure_escape(context.get('unsubscribe_email', ''))

        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        html_content = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title}</title>
    <style>
        /* Your original CSS remains unchanged */
{self._get_embedded_css()}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td>
                    <div class="container">
                        <div class="header">
                            <h1>{title}</h1>
                            <p class="subtitle">{subtitle}</p>
                        </div>"""

        if movies and len(movies) > 0:
            html_content += '''
                        <div class="section">
                            <div class="section-header">
                                <div class="section-icon">🎬</div>
                                <h2>New Movies</h2>
                                <div class="section-line"></div>
                            </div>'''

            for movie in movies:
                movie_html = self._render_movie_item(movie)
                html_content += movie_html

            html_content += '                        </div>'

        if tv_shows and len(tv_shows) > 0:
            html_content += '''
                        <div class="section">
                            <div class="section-header">
                                <div class="section-icon">📺</div>
                                <h2>New TV Episodes</h2>
                                <div class="section-line"></div>
                            </div>'''

            for show in tv_shows:
                show_html = self._render_tv_show_item(show, emby_url)
                html_content += show_html

            html_content += '                        </div>'

        if (not movies or len(movies) == 0) and (not tv_shows or len(tv_shows) == 0):
            html_content += '''
                        <div class="section">
                            <div class="no-items">
                                <div class="no-items-icon">🎭</div>
                                <h3>No New Content</h3>
                                <p>No new content has been added recently.<br>Check back soon for the latest movies and TV shows!</p>
                            </div>
                        </div>'''

        html_content += f'''
                        <div class="footer">
                            <div class="footer-logo">{emby_owner_name}</div>
                            <div class="footer-divider"></div>
                            <div class="footer-content">
                                <p>
                                    🎭 Enjoy your content on <a href="{emby_url}">{emby_owner_name}</a>
                                </p>
                                <p>
                                    📧 To unsubscribe, contact <a href="mailto:{unsubscribe_email}">{unsubscribe_email}</a>
                                </p>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>'''

        return html_content

    def _render_movie_item(self, movie: Dict[str, Any]) -> str:
        """Render a single movie item"""
        if not isinstance(movie, dict):
            logger.warning(f"Movie item is not a dictionary: {type(movie)}")
            return ""

        title = self._secure_escape(movie.get('title', 'Unknown'))
        year = self._secure_escape(movie.get('year', ''))
        overview = self._secure_escape(movie.get('tmdb_overview') or movie.get('overview', ''))
        poster_url = self._secure_escape(movie.get('tmdb_poster') or movie.get('poster_url', ''))

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster">'
        else:
            poster_html = '<div class="no-poster">No Poster<br>Available</div>'

        meta_parts = []
        if year:
            meta_parts.append(f'<span class="item-year">{year}</span>')

        meta_html = f'<div class="item-meta">{"".join(meta_parts)}</div>' if meta_parts else ''

        if overview and len(overview) > 300:
            overview = overview[:300] + "..."
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        genres_html = ''
        genres = movie.get('tmdb_genres') or movie.get('genres', [])
        if genres and isinstance(genres, list):
            genre_tags = []
            for genre in genres[:5]:
                if isinstance(genre, dict):
                    genre_name = self._secure_escape(genre.get('Name', ''))
                elif isinstance(genre, str):
                    genre_name = self._secure_escape(genre)
                else:
                    genre_name = self._secure_escape(str(genre))

                if genre_name:
                    genre_tags.append(f'<span class="genre-tag">{genre_name}</span>')

            if genre_tags:
                genres_html = f'<div class="genres">{"".join(genre_tags)}</div>'

        return f'''                            <div class="item">
                                <div class="item-poster">
                                    {poster_html}
                                </div>
                                <div class="item-content">
                                    <div class="item-title">{title}</div>
                                    {meta_html}
                                    {overview_html}
                                    {genres_html}
                                </div>
                            </div>'''

    def _render_tv_show_item(self, show: Dict[str, Any], emby_url: str) -> str:
        """Render a single TV show item"""
        if not isinstance(show, dict):
            logger.warning(f"TV show item is not a dictionary: {type(show)}")
            return ""

        title = self._secure_escape(show.get('title', 'Unknown'))
        overview = ''

        tmdb_data = show.get('tmdb_data', {})
        if isinstance(tmdb_data, dict) and tmdb_data.get('overview'):
            overview = self._secure_escape(tmdb_data['overview'])

        poster_url = ''

        if isinstance(tmdb_data, dict) and tmdb_data.get('poster_path'):
            poster_path = tmdb_data['poster_path']
            if poster_path.startswith('/'):
                poster_url = f"https://image.tmdb.org/t/p/w500{self._secure_escape(poster_path)}"
            else:
                poster_url = f"https://image.tmdb.org/t/p/w500/{self._secure_escape(poster_path)}"
        elif show.get('tmdb_poster'):
            poster_url = self._secure_escape(show['tmdb_poster'])
        elif show.get('poster_url'):
            poster_url = self._secure_escape(show['poster_url'])
        elif show.get('poster'):
            poster_url = self._secure_escape(show['poster'])
        elif show.get('id') and emby_url:
            item_id = self._secure_escape(show['id'])
            poster_url = f"{emby_url.rstrip('/')}/Items/{item_id}/Images/Primary?maxWidth=500"

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster">'
        else:
            poster_html = '<div class="no-poster">No Poster<br>Available</div>'

        if overview and len(overview) > 300:
            overview = overview[:300] + "..."
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        seasons_html = ''
        seasons = show.get('seasons', {})
        if isinstance(seasons, dict):
            season_parts = []
            for season_name, episodes in seasons.items():
                season_name_escaped = self._secure_escape(season_name)
                season_parts.append(f'<div class="tv-season"><h4>{season_name_escaped}</h4>')

                if isinstance(episodes, list):
                    for episode in episodes[:10]:
                        if isinstance(episode, dict):
                            episode_num = self._secure_escape(episode.get('episode_number', ''))
                            episode_name = self._secure_escape(episode.get('name', 'Unknown'))
                            episode_overview = self._secure_escape(episode.get('overview', ''))

                            if episode_overview and len(episode_overview) > 150:
                                episode_overview = episode_overview[:150] + "..."

                            episode_overview_html = f'<div class="episode-overview">{episode_overview}</div>' if episode_overview else ''

                            season_parts.append(f'''                                    <div class="episode">
                                        <div class="episode-title">Episode {episode_num}: {episode_name}</div>
                                        {episode_overview_html}
                                    </div>''')

                season_parts.append('                                </div>')

            seasons_html = f'<div class="tv-seasons">{"".join(season_parts)}</div>' if season_parts else ''

        return f'''                            <div class="item">
                                <div class="item-poster">
                                    {poster_html}
                                </div>
                                <div class="item-content">
                                    <div class="item-title">{title}</div>
                                    {overview_html}
                                    {seasons_html}
                                </div>
                            </div>'''

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize template context for security"""
        safe_context = {}

        for key, value in context.items():
            if key in ['movies', 'tv_shows']:
                safe_context[key] = self._sanitize_media_items(value)
            elif isinstance(value, str):
                safe_context[key] = self._sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                safe_context[key] = value
            elif value is None:
                safe_context[key] = ""
            else:
                safe_context[key] = self._sanitize_string(str(value))

        return safe_context

    def _sanitize_string(self, value: str) -> str:
        """Sanitize string values"""
        if not value:
            return ""

        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')

        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
            logger.warning(f"String truncated due to length: {len(value)} chars")

        return sanitized

    def _sanitize_media_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize movie/TV show items"""
        if not isinstance(items, list):
            return []

        sanitized_items = []
        for item in items[:100]:
            if not isinstance(item, dict):
                continue

            sanitized_item = {}
            for key, value in item.items():
                if isinstance(value, str):
                    sanitized_item[key] = self._sanitize_string(value)
                elif isinstance(value, (int, float, bool)):
                    sanitized_item[key] = value
                elif isinstance(value, dict):
                    sanitized_item[key] = self._sanitize_nested_dict(value)
                elif isinstance(value, list):
                    sanitized_item[key] = self._sanitize_list(value)
                elif value is None:
                    sanitized_item[key] = ""
                else:
                    sanitized_item[key] = self._sanitize_string(str(value))

            sanitized_items.append(sanitized_item)

        return sanitized_items

    def _sanitize_nested_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize nested dictionary data"""
        sanitized = {}

        if isinstance(data, str):
            return {'name': self._sanitize_string(data)}

        if not isinstance(data, dict):
            return {}

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = ""
            else:
                sanitized[key] = self._sanitize_string(str(value))

        return sanitized

    def _sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize list data"""
        sanitized = []

        for item in data[:50]:
            if isinstance(item, str):
                sanitized.append(self._sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_nested_dict(item))
            elif isinstance(item, (int, float, bool)):
                sanitized.append(item)
            elif item is None:
                sanitized.append("")
            else:
                sanitized.append(self._sanitize_string(str(item)))

        return sanitized

    def _get_embedded_css(self) -> str:
        """
        Returns your original embedded CSS
        """
        # Place your large CSS block here as a string.
        # To keep this message short, I've omitted it.
        # In your file, keep the original CSS block.
        return """
        [YOUR ORIGINAL CSS BLOCK]
        """


# Global template renderer instance
template_renderer = SecureTemplateRenderer()
