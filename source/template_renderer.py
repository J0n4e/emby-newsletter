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

# Set logging level to DEBUG to see the new debug messages
logging.basicConfig(level=logging.DEBUG)


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

        original_escaped = escaped  # Store original to check if modified
        for pattern, replacement in dangerous_patterns:
            escaped = escaped.replace(pattern.lower(), replacement)
            escaped = escaped.replace(pattern.upper(), replacement.upper())
            escaped = escaped.replace(pattern.capitalize(), replacement.capitalize())

        if escaped != original_escaped:
            logger.debug(
                f"Secure escape modified string. Original (partial): '{original_escaped[:50]}...', Modified (partial): '{escaped[:50]}...'")

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

        # Build the complete HTML email
        html_content = f"""<!DOCTYPE html>
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
            color: rgb(229, 231, 235);
            margin: 0;
            padding: 0;
            background: rgb(10, 10, 10);
        }}

        .email-wrapper {{
            background: rgb(10, 10, 10);
            min-height: 100vh;
            padding: 20px 0;
        }}

        .container {{
            max-width: 680px;
            margin: 0 auto;
            background: rgb(17, 24, 39);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
        }}

        .header {{
            background: linear-gradient(135deg, rgb(153, 27, 27) 0%, rgb(220, 38, 38) 50%, rgb(239, 68, 68) 100%);
            padding: 48px 40px;
            text-align: center;
        }}

        .header h1 {{
            color: rgb(255, 255, 255);
            margin: 0 0 12px 0;
            font-size: 2.75em;
            font-weight: 700;
            text-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}

        .header .subtitle {{
            color: rgba(255, 255, 255, 0.9);
            margin: 0;
            font-size: 1.125em;
            font-weight: 400;
        }}

        .section {{
            padding: 48px 40px;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 32px;
            gap: 16px;
        }}

        .section h2 {{
            color: rgb(249, 250, 251);
            font-size: 1.875em;
            font-weight: 600;
            margin: 0;
        }}

        .section-icon {{
            background: linear-gradient(135deg, rgb(220, 38, 38) 0%, rgb(239, 68, 68) 100%);
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            box-shadow: 0 8px 16px rgba(220, 38, 38, 0.3);
        }}

        .section-line {{
            flex: 1;
            height: 2px;
            background: linear-gradient(90deg, rgb(220, 38, 38) 0%, rgba(220, 38, 38, 0.2) 100%);
        }}

        .item {{
            background: linear-gradient(145deg, rgb(31, 41, 55) 0%, rgb(55, 65, 81) 100%);
            margin: 24px 0;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(220, 38, 38, 0.15);
            display: table;
            width: 100%;
            table-layout: fixed;
        }}

        .item-poster {{
            display: table-cell;
            width: 140px;
            height: 210px;
            vertical-align: top;
            padding: 0;
        }}

        .item-poster img {{
            width: 140px;
            height: 210px;
            object-fit: cover;
            display: block;
        }}

        .no-poster {{
            width: 140px;
            height: 210px;
            background: linear-gradient(145deg, rgb(55, 65, 81) 0%, rgb(75, 85, 99) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgb(156, 163, 175);
            font-size: 0.875em;
            text-align: center;
            font-weight: 500;
        }}

        .item-content {{
            display: table-cell;
            padding: 32px;
            vertical-align: top;
        }}

        .item-title {{
            font-size: 1.5em;
            font-weight: 700;
            color: rgb(249, 250, 251);
            margin-bottom: 8px;
            line-height: 1.3;
        }}

        .item-meta {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }}

        .item-year {{
            background: rgba(220, 38, 38, 0.15);
            color: rgb(252, 165, 165);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875em;
            font-weight: 500;
            border: 1px solid rgba(220, 38, 38, 0.3);
        }}

        .item-overview {{
            color: rgb(209, 213, 219);
            font-size: 0.9375em;
            line-height: 1.6;
            margin-bottom: 24px;
            font-weight: 400;
        }}

        .genres {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: auto;
        }}

        .genre-tag {{
            background: linear-gradient(135deg, rgb(220, 38, 38) 0%, rgb(239, 68, 68) 100%);
            color: rgb(255, 255, 255);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8125em;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(220, 38, 38, 0.3);
        }}

        .tv-seasons {{
            margin-top: 24px;
        }}

        .tv-season {{
            background: rgba(220, 38, 38, 0.08);
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            border-left: 4px solid rgb(220, 38, 38);
        }}

        .tv-season h4 {{
            color: rgb(248, 113, 113);
            margin: 0 0 16px 0;
            font-size: 1.125em;
            font-weight: 600;
        }}

        .episode {{
            background: rgba(255, 255, 255, 0.04);
            padding: 16px 20px;
            margin: 8px 0;
            border-radius: 10px;
            border-left: 3px solid rgb(220, 38, 38);
        }}

        .episode-title {{
            color: rgb(248, 113, 113);
            font-weight: 600;
            font-size: 0.9375em;
            margin-bottom: 6px;
        }}

        .episode-overview {{
            color: rgb(209, 213, 219);
            font-size: 0.875em;
            line-height: 1.5;
            font-weight: 400;
        }}

        .footer {{
            background: linear-gradient(135deg, rgb(15, 23, 42) 0%, rgb(30, 41, 59) 100%);
            text-align: center;
            padding: 48px 40px;
        }}

        .footer-logo {{
            font-size: 1.5em;
            font-weight: 700;
            color: rgb(239, 68, 68);
            margin-bottom: 16px;
        }}

        .footer-content {{
            color: rgb(156, 163, 175);
            font-size: 0.9375em;
            line-height: 1.6;
        }}

        .footer a {{
            color: rgb(239, 68, 68);
            text-decoration: none;
            font-weight: 500;
        }}

        .footer-divider {{
            height: 1px;
            background: rgba(255, 255, 255, 0.1);
            margin: 24px 0;
        }}

        .no-items {{
            text-align: center;
            color: rgb(156, 163, 175);
            padding: 80px 40px;
            background: rgba(220, 38, 38, 0.05);
            border-radius: 16px;
            margin: 24px 0;
            border: 1px solid rgba(220, 38, 38, 0.15);
        }}

        .no-items-icon {{
            font-size: 4em;
            margin-bottom: 24px;
            opacity: 0.6;
        }}

        .no-items h3 {{
            font-size: 1.5em;
            font-weight: 600;
            color: rgb(249, 250, 251);
            margin: 0 0 8px 0;
        }}

        .no-items p {{
            font-size: 1em;
            margin: 0;
            line-height: 1.6;
        }}

        @media only screen and (max-width: 640px) {{
            .email-wrapper {{
                padding: 10px;
            }}

            .header {{
                padding: 32px 24px;
            }}

            .header h1 {{
                font-size: 2.25em;
            }}

            .section {{
                padding: 32px 24px;
            }}

            .section h2 {{
                font-size: 1.5em;
            }}

            .section-icon {{
                width: 40px;
                height: 40px;
                font-size: 1.25em;
            }}

            .item {{
                display: block;
                margin: 20px 0;
            }}

            .item-poster {{
                display: block;
                width: 100%;
                height: 240px;
                text-align: center;
            }}

            .item-poster img {{
                width: auto;
                height: 240px;
                max-width: 100%;
            }}

            .no-poster {{
                width: 100%;
                height: 240px;
            }}

            .item-content {{
                display: block;
                padding: 24px;
            }}

            .tv-season {{
                padding: 20px;
            }}

            .footer {{
                padding: 32px 24px;
            }}
        }}
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

        # Movies section
        if movies and len(movies) > 0:
            html_content += '''
                        <div class="section">
                            <div class="section-header">
                                <div class="section-icon">汐</div>
                                <h2>New Movies</h2>
                                <div class="section-line"></div>
                            </div>'''

            for movie in movies:
                movie_html = self._render_movie_item(movie)
                html_content += movie_html

            html_content += '                        </div>'

        # TV Shows section
        if tv_shows and len(tv_shows) > 0:
            html_content += '''
                        <div class="section">
                            <div class="section-header">
                                <div class="section-icon">銅</div>
                                <h2>New TV Episodes</h2>
                                <div class="section-line"></div>
                            </div>'''

            for show in tv_shows:
                show_html = self._render_tv_show_item(show)
                html_content += show_html

            html_content += '                        </div>'

        # No content message
        if (not movies or len(movies) == 0) and (not tv_shows or len(tv_shows) == 0):
            html_content += '''
                        <div class="section">
                            <div class="no-items">
                                <div class="no-items-icon">鹿</div>
                                <h3>No New Content</h3>
                                <p>No new content has been added recently.<br>Check back soon for the latest movies and TV shows!</p>
                            </div>
                        </div>'''

        # Footer
        html_content += f'''
                        <div class="footer">
                            <div class="footer-logo">{emby_owner_name}</div>
                            <div class="footer-divider"></div>
                            <div class="footer-content">
                                <p>
                                    鹿 Enjoy your content on <a href="{emby_url}">{emby_owner_name}</a>
                                </p>
                                <p>
                                    透 To unsubscribe, contact <a href="mailto:{unsubscribe_email}">{unsubscribe_email}</a>
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

        # Build poster HTML
        if poster_url:
            # Add data-original-url for debugging
            poster_html = f'<img src="{poster_url}" alt="{title} poster" data-original-url="{poster_url}">'
        else:
            poster_html = '<div class="no-poster">No Poster<br>Available</div>'

        # Build meta information
        meta_parts = []
        if year:
            meta_parts.append(f'<span class="item-year">{year}</span>')

        meta_html = f'<div class="item-meta">{"".join(meta_parts)}</div>' if meta_parts else ''

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

        # Build poster HTML - improved logic for TV shows
        poster_url = ''
        original_poster_url_debug = ''  # For debugging

        logger.debug(f"Attempting to find poster for TV show: {title}")
        logger.debug(
            f"Raw show data for poster check: {show.get('tmdb_data')} | {show.get('tmdb_poster')} | {show.get('poster_url')} | {show.get('poster')}")

        # Try multiple sources for poster URL
        if isinstance(tmdb_data, dict) and tmdb_data.get('poster_path'):
            # TMDB poster path
            poster_path = tmdb_data['poster_path']
            # Ensure poster_path starts with '/' for correct TMDB URL construction
            if poster_path and not poster_path.startswith('/'):
                poster_path = '/' + poster_path
            original_poster_url_debug = f"https://image.tmdb.org/t/p/w500{poster_path}"
            poster_url = self._secure_escape(original_poster_url_debug)
            logger.debug(f"Using TMDB poster_path: {poster_path}, constructed URL: {poster_url}")
        elif show.get('tmdb_poster'):
            # Direct TMDB poster URL
            original_poster_url_debug = show['tmdb_poster']
            poster_url = self._secure_escape(original_poster_url_debug)
            logger.debug(f"Using direct tmdb_poster: {poster_url}")
        elif show.get('poster_url'):
            # Fallback to general poster URL
            original_poster_url_debug = show['poster_url']
            poster_url = self._secure_escape(original_poster_url_debug)
            logger.debug(f"Using general poster_url: {poster_url}")
        elif show.get('poster'):
            # Another fallback
            original_poster_url_debug = show['poster']
            poster_url = self._secure_escape(original_poster_url_debug)
            logger.debug(f"Using fallback poster: {poster_url}")

        if not poster_url:
            logger.debug(f"No valid poster URL found for TV show: {title}")

        if poster_url:
            # Add data-original-url for debugging in browser developer tools
            poster_html = f'<img src="{poster_url}" alt="{title} poster" data-original-url="{original_poster_url_debug}">'
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
