#!/usr/bin/env python3
"""
Simplified template rendering for Emby Newsletter using Jinja2
"""

import os
import logging
import html
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("Jinja2 not available, using fallback template renderer")


class SecureTemplateRenderer:
    """Secure template renderer using Jinja2 or fallback"""

    def __init__(self, template_dir: str = "/app/templates"):
        """Initialize the template renderer"""
        self.template_dir = template_dir

        if JINJA2_AVAILABLE:
            # Configure Jinja2 environment with security settings
            self.jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )

            # Add custom filters
            self.jinja_env.filters['e'] = html.escape
        else:
            self.jinja_env = None

    def render_email_template(self, context: Dict[str, Any]) -> str:
        """Render the email template with secure context"""
        try:
            # Sanitize context data
            safe_context = self._sanitize_context(context)

            if JINJA2_AVAILABLE and self.jinja_env:
                # Use Jinja2 for proper template rendering
                return self._render_with_jinja2(safe_context)
            else:
                # Fallback to built-in template
                return self._build_html_email(safe_context)

        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            # Always fall back to built-in template on error
            safe_context = self._sanitize_context(context)
            return self._build_html_email(safe_context)

    def _render_with_jinja2(self, context: Dict[str, Any]) -> str:
        """Render template using Jinja2"""
        try:
            template_path = os.path.join(self.template_dir, 'email.html')

            if os.path.exists(template_path):
                # Load template from file
                template = self.jinja_env.get_template('email.html')
                html_content = template.render(**context)
                logger.debug("Email template rendered successfully with Jinja2")
                return html_content
            else:
                logger.warning(f"Template file not found at {template_path}, using built-in template")
                return self._build_html_email(context)

        except Exception as e:
            logger.error(f"Jinja2 rendering failed: {e}")
            return self._build_html_email(context)

    def _build_html_email(self, context: Dict[str, Any]) -> str:
        """Build HTML email using secure string construction (fallback)"""
        # Escape all context values
        title = html.escape(str(context.get('title', 'Emby Newsletter')))
        subtitle = html.escape(str(context.get('subtitle', '')))
        language = html.escape(str(context.get('language', 'en')))
        emby_url = html.escape(str(context.get('emby_url', '')))
        emby_owner_name = html.escape(str(context.get('emby_owner_name', '')))
        unsubscribe_email = html.escape(str(context.get('unsubscribe_email', '')))

        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        # Build HTML content
        html_content = f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #ffffff;
            max-width: 800px;
            margin: 0 auto;
            padding: 0;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
            min-height: 100vh;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
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
            position: relative;
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
                    </div>'''

        # Movies section
        if movies and len(movies) > 0:
            html_content += '''
                    <div class="section">
                        <h2>🎬 New Movies</h2>'''

            for movie in movies:
                html_content += self._render_movie_item(movie)

            html_content += '''
                    </div>'''

        # TV Shows section
        if tv_shows and len(tv_shows) > 0:
            html_content += '''
                    <div class="section">
                        <h2>📺 New TV Episodes</h2>'''

            for show in tv_shows:
                html_content += self._render_tv_show_item(show)

            html_content += '''
                    </div>'''

        # No content message
        if (not movies or len(movies) == 0) and (not tv_shows or len(tv_shows) == 0):
            html_content += '''
                    <div class="section">
                        <div class="no-items">
                            <p>No new content has been added recently.</p>
                            <p>Check back soon for the latest movies and TV shows!</p>
                        </div>
                    </div>'''

        # Footer
        html_content += f'''
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
</html>'''

        return html_content

    def _render_movie_item(self, movie: Dict[str, Any]) -> str:
        """Render a single movie item"""
        if not isinstance(movie, dict):
            return ""

        title = html.escape(str(movie.get('title', 'Unknown')))
        year = html.escape(str(movie.get('year', '')))
        overview = html.escape(str(movie.get('tmdb_overview') or movie.get('overview', '')))

        # Handle poster URL
        poster_url = movie.get('tmdb_poster') or movie.get('poster_url', '')
        if poster_url:
            poster_url = html.escape(str(poster_url))
            poster_html = f'<img src="{poster_url}" alt="{title} poster" style="width: 120px; height: 180px; object-fit: cover; display: block;">'
        else:
            poster_html = '<div style="width: 120px; height: 180px; background: linear-gradient(135deg, #262626 0%, #404040 100%); display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.8em; text-align: center; border-radius: 8px;">No Poster<br>Available</div>'

        # Year HTML
        year_html = f'<div class="item-year">({year})</div>' if year else ''

        # Overview HTML (truncate if too long)
        if overview and len(overview) > 300:
            overview = overview[:300] + "..."
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        # Genres HTML
        genres_html = ''
        genres = movie.get('tmdb_genres') or movie.get('genres', [])
        if genres and isinstance(genres, list):
            genre_tags = []
            for genre in genres[:5]:  # Limit to 5 genres
                if isinstance(genre, dict):
                    genre_name = html.escape(str(genre.get('Name', '')))
                elif isinstance(genre, str):
                    genre_name = html.escape(genre)
                else:
                    genre_name = html.escape(str(genre))

                if genre_name:
                    genre_tags.append(f'<span class="genre-tag">{genre_name}</span>')

            if genre_tags:
                genres_html = f'<div>{"".join(genre_tags)}</div>'

        return f'''
                        <div class="item">
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
            return ""

        title = html.escape(str(show.get('title', 'Unknown')))

        # Get overview from TMDB data if available
        overview = ''
        tmdb_data = show.get('tmdb_data', {})
        if isinstance(tmdb_data, dict) and tmdb_data.get('overview'):
            overview = html.escape(str(tmdb_data['overview']))

        # Handle poster URL
        poster_url = ''
        if isinstance(tmdb_data, dict) and tmdb_data.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w500{html.escape(str(tmdb_data['poster_path']))}"
        elif show.get('poster_url'):
            poster_url = html.escape(str(show['poster_url']))

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster" style="width: 120px; height: 180px; object-fit: cover; display: block;">'
        else:
            poster_html = '<div style="width: 120px; height: 180px; background: linear-gradient(135deg, #262626 0%, #404040 100%); display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.8em; text-align: center; border-radius: 8px;">No Poster<br>Available</div>'

        # Overview HTML (truncate if too long)
        if overview and len(overview) > 300:
            overview = overview[:300] + "..."
        overview_html = f'<div class="item-overview">{overview}</div>' if overview else ''

        # Seasons HTML
        seasons_html = ''
        seasons = show.get('seasons', {})
        if isinstance(seasons, dict):
            for season_name, episodes in seasons.items():
                season_name_escaped = html.escape(str(season_name))
                seasons_html += f'<div class="tv-season"><h4>{season_name_escaped}</h4>'

                if isinstance(episodes, list):
                    for episode in episodes[:10]:  # Limit episodes per season
                        if isinstance(episode, dict):
                            episode_num = html.escape(str(episode.get('episode_number', '')))
                            episode_name = html.escape(str(episode.get('name', 'Unknown')))
                            episode_overview = html.escape(str(episode.get('overview', '')))

                            # Truncate episode overview
                            if episode_overview and len(episode_overview) > 150:
                                episode_overview = episode_overview[:150] + "..."

                            episode_overview_html = f'<div class="episode-overview">{episode_overview}</div>' if episode_overview else ''

                            seasons_html += f'''<div class="episode">
                                    <strong>Episode {episode_num}: {episode_name}</strong>
                                    {episode_overview_html}
                                </div>'''

                seasons_html += '</div>'

        return f'''
                        <div class="item">
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
        if isinstance(data, str):
            return {'name': self._sanitize_string(data)}
        if not isinstance(data, dict):
            return {}

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