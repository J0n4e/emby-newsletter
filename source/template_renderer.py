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

        # Convert to string and escape
        str_value = str(value)

        # HTML escape
        escaped = html.escape(str_value, quote=True)

        # Additional security: escape potential script injections
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
            # Sanitize context data
            safe_context = self._sanitize_context(context)

            # Generate HTML using secure string building
            html_content = self._build_html_email(safe_context)

            logger.debug("Email template rendered successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            raise

    def _build_html_email(self, context: Dict[str, Any]) -> str:
        """Build HTML email using secure string construction"""
        # Escape all context values
        title = self._secure_escape(context.get('title', 'Emby Newsletter'))
        subtitle = self._secure_escape(context.get('subtitle', ''))
        language = self._secure_escape(context.get('language', 'en'))
        emby_url = self._secure_escape(context.get('emby_url', ''))
        emby_owner_name = self._secure_escape(context.get('emby_owner_name', ''))
        unsubscribe_email = self._secure_escape(context.get('unsubscribe_email', ''))

        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        # Build HTML structure
        html_parts = []

        # HTML header
        html_parts.append(f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
        }}
        .header p {{
            color: #7f8c8d;
            margin: 10px 0 0 0;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .item {{
            display: flex;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .item-poster {{
            flex-shrink: 0;
            margin-right: 20px;
        }}
        .item-poster img {{
            width: 100px;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
        }}
        .item-content {{
            flex: 1;
        }}
        .item-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .item-year {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .item-overview {{
            margin-top: 10px;
            color: #555;
        }}
        .item-genres {{
            margin-top: 10px;
        }}
        .genre-tag {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
        }}
        .tv-season {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        .tv-season h4 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .episode {{
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #27ae60;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .footer a {{
            color: #3498db;
            text-decoration: none;
        }}
        .no-items {{
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            padding: 20px;
        }}
        @media (max-width: 600px) {{
            .item {{
                flex-direction: column;
            }}
            .item-poster {{
                margin-right: 0;
                margin-bottom: 15px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>''')

        # Movies section
        if movies:
            html_parts.append('''
        <div class="section">
            <h2>🎬 New Movies</h2>''')

            for movie in movies:
                movie_html = self._render_movie_item(movie)
                html_parts.append(movie_html)

            html_parts.append('        </div>')

        # TV Shows section
        if tv_shows:
            html_parts.append('''
        <div class="section">
            <h2>📺 New TV Episodes</h2>''')

            for show in tv_shows:
                show_html = self._render_tv_show_item(show)
                html_parts.append(show_html)

            html_parts.append('        </div>')

        # No content message
        if not movies and not tv_shows:
            html_parts.append('''
        <div class="no-items">
            <p>No new content has been added recently.</p>
        </div>''')

        # Footer
        html_parts.append(f'''
        <div class="footer">
            <p>
                Enjoy your content on <a href="{emby_url}">{emby_owner_name}</a>
            </p>
            <p>
                <small>
                    To unsubscribe, please contact <a href="mailto:{unsubscribe_email}">{unsubscribe_email}</a>
                </small>
            </p>
        </div>
    </div>
</body>
</html>''')

        return '\n'.join(html_parts)

    def _render_movie_item(self, movie: Dict[str, Any]) -> str:
        """Render a single movie item"""
        title = self._secure_escape(movie.get('title', 'Unknown'))
        year = self._secure_escape(movie.get('year', ''))
        overview = self._secure_escape(movie.get('tmdb_overview') or movie.get('overview', ''))
        poster_url = self._secure_escape(movie.get('tmdb_poster') or movie.get('poster_url', ''))

        # Build poster HTML
        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster">'
        else:
            poster_html = '<div style="width: 100px; height: 150px; background: #ddd; border-radius: 5px; display: flex; align-items: center; justify-content: center; color: #999;">No Image</div>'

        # Build year HTML
        year_html = f'<div class="item-year">({year})</div>' if year else ''

        # Build overview HTML
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        # Build genres HTML
        genres_html = ''
        genres = movie.get('tmdb_genres') or movie.get('genres', [])
        if genres:
            genre_tags = []
            for genre in genres[:5]:  # Limit to 5 genres
                genre_name = self._secure_escape(genre if isinstance(genre, str) else genre.get('Name', ''))
                if genre_name:
                    genre_tags.append(f'<span class="genre-tag">{genre_name}</span>')

            if genre_tags:
                genres_html = f'<div class="item-genres">{"".join(genre_tags)}</div>'

        return f'''            <div class="item">
                <div class="item-poster">
                    {poster_html}
                </div>
                <div class="item-content">
                    <div class="item-title">{title}</div>
                    {year_html}
                    {overview_html}
                    {genres_html}
                </div>
            </div>'''

    def _render_tv_show_item(self, show: Dict[str, Any]) -> str:
        """Render a single TV show item"""
        title = self._secure_escape(show.get('title', 'Unknown'))
        overview = ''

        # Get overview from TMDB data if available
        tmdb_data = show.get('tmdb_data', {})
        if tmdb_data and tmdb_data.get('overview'):
            overview = self._secure_escape(tmdb_data['overview'])

        # Build poster HTML
        poster_url = ''
        if tmdb_data and tmdb_data.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w500{self._secure_escape(tmdb_data['poster_path'])}"
        elif show.get('poster_url'):
            poster_url = self._secure_escape(show['poster_url'])

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster">'
        else:
            poster_html = '<div style="width: 100px; height: 150px; background: #ddd; border-radius: 5px; display: flex; align-items: center; justify-content: center; color: #999;">No Image</div>'

        # Build overview HTML
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        # Build seasons HTML
        seasons_html = ''
        seasons = show.get('seasons', {})
        if seasons:
            season_parts = []
            for season_name, episodes in seasons.items():
                season_name_escaped = self._secure_escape(season_name)
                season_parts.append(f'<div class="tv-season"><h4>{season_name_escaped}</h4>')

                for episode in episodes[:10]:  # Limit episodes per season
                    episode_num = self._secure_escape(episode.get('episode_number', ''))
                    episode_name = self._secure_escape(episode.get('name', 'Unknown'))
                    episode_overview = self._secure_escape(episode.get('overview', ''))

                    episode_overview_html = f'<div style="margin-top: 5px; font-size: 0.9em; color: #666;">{episode_overview}</div>' if episode_overview else ''

                    season_parts.append(f'''<div class="episode">
                            <strong>Episode {episode_num}: {episode_name}</strong>
                            {episode_overview_html}
                        </div>''')

                season_parts.append('</div>')

            seasons_html = ''.join(season_parts)

        return f'''            <div class="item">
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
                # Sanitize movie/TV show data
                safe_context[key] = self._sanitize_media_items(value)
            elif isinstance(value, str):
                # Basic string sanitization
                safe_context[key] = self._sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                # Safe data types
                safe_context[key] = value
            elif value is None:
                safe_context[key] = ""
            else:
                # Convert other types to string and sanitize
                safe_context[key] = self._sanitize_string(str(value))

        return safe_context

    def _sanitize_string(self, value: str) -> str:
        """Sanitize string values"""
        if not value:
            return ""

        # Remove null bytes and control characters
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')

        # Limit length to prevent DoS
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

        for item in items[:100]:  # Limit number of items
            if not isinstance(item, dict):
                continue

            sanitized_item = {}

            # Sanitize each field in the item
            for key, value in item.items():
                if isinstance(value, str):
                    sanitized_item[key] = self._sanitize_string(value)
                elif isinstance(value, (int, float, bool)):
                    sanitized_item[key] = value
                elif isinstance(value, dict):
                    # Handle nested dictionaries (like tmdb_data)
                    sanitized_item[key] = self._sanitize_nested_dict(value)
                elif isinstance(value, list):
                    # Handle lists (like genres)
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

        for item in data[:50]:  # Limit list size
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


# Global template renderer instance
template_renderer = SecureTemplateRenderer()