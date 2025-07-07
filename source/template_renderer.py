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

            # Always use built-in template for simplicity and security
            html_content = self._build_html_email(safe_context)
            logger.debug("Email template rendered successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            # Fallback to built-in template on error
            safe_context = self._sanitize_context(context)
            return self._build_html_email(safe_context)

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

        # HTML header with modern styling
        html_parts.append(f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #ffffff;
            max-width: 800px;
            margin: 0 auto;
            padding: 0;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
            min-height: 100vh;
        }}
        .container {{
            background: linear-gradient(145deg, #141414 0%, #1f1f1f 100%);
            margin: 0;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            border-radius: 0;
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 50%, #f87171 100%);
            text-align: center;
            padding: 40px 30px;
        }}
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
        }}
        .header p {{
            color: rgba(255, 255, 255, 0.9);
            margin: 15px 0 0 0;
            font-size: 1.1em;
            font-weight: 300;
        }}
        .section {{
            padding: 40px 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .section h2 {{
            color: #ef4444;
            font-size: 1.8em;
            font-weight: 600;
            margin: 0 0 30px 0;
            padding-bottom: 15px;
            border-bottom: 3px solid rgba(239, 68, 68, 0.4);
        }}
        .item {{
            background: linear-gradient(145deg, #1a1a1a 0%, #262626 100%);
            margin: 25px 0;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(239, 68, 68, 0.2);
            display: table;
            width: 100%;
            table-layout: fixed;
        }}
        .item-poster {{
            display: table-cell;
            width: 120px;
            height: 180px;
            vertical-align: top;
            padding: 0;
        }}
        .item-poster img {{
            width: 120px;
            height: 180px;
            object-fit: cover;
            display: block;
        }}
        .no-poster {{
            width: 120px;
            height: 180px;
            background: linear-gradient(135deg, #262626 0%, #404040 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 0.8em;
            text-align: center;
            border-radius: 8px;
        }}
        .item-content {{
            display: table-cell;
            padding: 25px;
            vertical-align: top;
        }}
        .item-title {{
            font-size: 1.4em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
            line-height: 1.3;
        }}
        .item-year {{
            color: #fca5a5;
            font-size: 0.95em;
            font-weight: 500;
            margin-bottom: 15px;
        }}
        .item-overview {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 0.95em;
            line-height: 1.5;
            margin-bottom: 20px;
        }}
        .genre-tag {{
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
            margin-right: 8px;
            margin-bottom: 8px;
            display: inline-block;
        }}
        .tv-season {{
            margin: 20px 0;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #ef4444;
        }}
        .tv-season h4 {{
            color: #fca5a5;
            margin: 0 0 15px 0;
            font-size: 1.2em;
            font-weight: 600;
        }}
        .episode {{
            background: rgba(255, 255, 255, 0.08);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 3px solid #dc2626;
        }}
        .episode strong {{
            color: #fca5a5;
            font-weight: 600;
        }}
        .episode-overview {{
            margin-top: 8px;
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.4;
        }}
        .footer {{
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
            text-align: center;
            padding: 40px 30px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9em;
        }}
        .footer a {{
            color: #ef4444;
            text-decoration: none;
            font-weight: 500;
        }}
        .footer-logo {{
            font-size: 1.5em;
            font-weight: 700;
            color: #ef4444;
            margin-bottom: 15px;
        }}
        .no-items {{
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            font-style: italic;
            padding: 60px 20px;
            background: rgba(239, 68, 68, 0.05);
            border-radius: 15px;
            margin: 20px 0;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }}
        @media only screen and (max-width: 600px) {{
            .item {{
                display: block;
            }}
            .item-poster {{
                display: block;
                width: 100%;
                height: 200px;
                text-align: center;
            }}
            .item-poster img {{
                width: auto;
                height: 200px;
                max-width: 100%;
            }}
            .no-poster {{
                width: 100%;
                height: 200px;
            }}
            .item-content {{
                display: block;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td>
                <div class="container">
                    <div class="header">
                        <h1>{title}</h1>
                        <p>{subtitle}</p>
                    </div>''')

        # Movies section
        if movies and len(movies) > 0:
            html_parts.append('''
                    <div class="section">
                        <h2>🎬 New Movies</h2>''')

            for movie in movies:
                movie_html = self._render_movie_item(movie)
                html_parts.append(movie_html)

            html_parts.append('                    </div>')

        # TV Shows section
        if tv_shows and len(tv_shows) > 0:
            html_parts.append('''
                    <div class="section">
                        <h2>📺 New TV Episodes</h2>''')

            for show in tv_shows:
                show_html = self._render_tv_show_item(show)
                html_parts.append(show_html)

            html_parts.append('                    </div>')

        # No content message
        if (not movies or len(movies) == 0) and (not tv_shows or len(tv_shows) == 0):
            html_parts.append('''
                    <div class="section">
                        <div class="no-items">
                            <p>No new content has been added recently.</p>
                            <p>Check back soon for the latest movies and TV shows!</p>
                        </div>
                    </div>''')

        # Footer
        html_parts.append(f'''
                    <div class="footer">
                        <div class="footer-logo">{emby_owner_name}</div>
                        <p>
                            🎭 Enjoy your content on <a href="{emby_url}">{emby_owner_name}</a>
                        </p>
                        <p>
                            <small>
                                📧 To unsubscribe, contact <a href="mailto:{unsubscribe_email}">{unsubscribe_email}</a>
                            </small>
                        </p>
                    </div>
                </div>
            </td>
        </tr>
    </table>
</body>
</html>''')

        return '\n'.join(html_parts)

    def _render_movie_item(self, movie: Dict[str, Any]) -> str:
        """Render a single movie item"""
        if not isinstance(movie, dict):
            logger.warning(f"Movie item is not a dictionary: {type(movie)}")
            return ""

        title = self._secure_escape(movie.get('title', 'Unknown'))
        year = self._secure_escape(movie.get('year', ''))
        overview = self._secure_escape(movie.get('tmdb_overview') or movie.get('overview', ''))
        poster_url = self._secure_escape(movie.get('tmdb_poster') or movie.get('poster_url', ''))

        # Build poster HTML
        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster">'
        else:
            poster_html = '<div class="no-poster">No Poster<br>Available</div>'

        # Build year HTML
        year_html = f'<div class="item-year">({year})</div>' if year else ''

        # Build overview HTML (truncate if too long)
        if overview and len(overview) > 300:
            overview = overview[:300] + "..."
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        # Build genres HTML
        genres_html = ''
        genres = movie.get('tmdb_genres') or movie.get('genres', [])
        if genres and isinstance(genres, list):
            genre_tags = []
            for genre in genres[:5]:  # Limit to 5 genres
                if isinstance(genre, dict):
                    genre_name = self._secure_escape(genre.get('Name', ''))
                elif isinstance(genre, str):
                    genre_name = self._secure_escape(genre)
                else:
                    genre_name = self._secure_escape(str(genre))

                if genre_name:
                    genre_tags.append(f'<span class="genre-tag">{genre_name}</span>')

            if genre_tags:
                genres_html = f'<div>{"".join(genre_tags)}</div>'

        return f'''                        <div class="item">
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
        if not isinstance(show, dict):
            logger.warning(f"TV show item is not a dictionary: {type(show)}")
            return ""

        title = self._secure_escape(show.get('title', 'Unknown'))
        overview = ''

        # Get overview from TMDB data if available
        tmdb_data = show.get('tmdb_data', {})
        if isinstance(tmdb_data, dict) and tmdb_data.get('overview'):
            overview = self._secure_escape(tmdb_data['overview'])

        # Build poster HTML
        poster_url = ''
        if isinstance(tmdb_data, dict) and tmdb_data.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w500{self._secure_escape(tmdb_data['poster_path'])}"
        elif show.get('poster_url'):
            poster_url = self._secure_escape(show['poster_url'])

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster">'
        else:
            poster_html = '<div class="no-poster">No Poster<br>Available</div>'

        # Build overview HTML (truncate if too long)
        if overview and len(overview) > 300:
            overview = overview[:300] + "..."
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        # Build seasons HTML
        seasons_html = ''
        seasons = show.get('seasons', {})
        if isinstance(seasons, dict):
            season_parts = []
            for season_name, episodes in seasons.items():
                season_name_escaped = self._secure_escape(season_name)
                season_parts.append(f'<div class="tv-season"><h4>{season_name_escaped}</h4>')

                if isinstance(episodes, list):
                    for episode in episodes[:10]:  # Limit episodes per season
                        if isinstance(episode, dict):
                            episode_num = self._secure_escape(episode.get('episode_number', ''))
                            episode_name = self._secure_escape(episode.get('name', 'Unknown'))
                            episode_overview = self._secure_escape(episode.get('overview', ''))

                            # Truncate episode overview
                            if episode_overview and len(episode_overview) > 150:
                                episode_overview = episode_overview[:150] + "..."

                            episode_overview_html = f'<div class="episode-overview">{episode_overview}</div>' if episode_overview else ''

                            season_parts.append(f'''                                <div class="episode">
                                    <strong>Episode {episode_num}: {episode_name}</strong>
                                    {episode_overview_html}
                                </div>''')

                season_parts.append('                            </div>')

            seasons_html = ''.join(season_parts)

        return f'''                        <div class="item">
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

        # Handle case where data might be a string instead of dict
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