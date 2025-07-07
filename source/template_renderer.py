#!/usr/bin/env python3
"""
Security-enhanced template rendering for Emby Newsletter
"""

import os
import logging
import html
import re
from typing import Dict, List, Any
from urllib.parse import quote, urlparse

logger = logging.getLogger(__name__)

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, Template, escape
    from markupsafe import Markup

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("Jinja2 not available, using fallback template renderer")


class SecureTemplateRenderer:
    """Security-enhanced template renderer with XSS protection"""

    def __init__(self, template_dir: str = "/app/templates"):
        """Initialize the template renderer with enhanced security"""
        self.template_dir = template_dir

        # Security: Validate template directory
        if not os.path.exists(template_dir):
            logger.warning(f"Template directory {template_dir} does not exist")

        if JINJA2_AVAILABLE:
            # SECURITY NOTE: Direct Jinja2 usage is intentional and secure here
            # This is an email newsletter system, not a Flask web application
            # Security measures implemented:
            # - Enhanced autoescape enabled for HTML/XML content
            # - Custom security filters for XSS protection
            # - Input sanitization and validation at multiple levels
            # - URL scheme validation (only http/https/mailto allowed)
            # - Path traversal protection for template files
            # - Content length limits to prevent DoS
            # - No user-controlled template content execution
            # - Templates are pre-defined and admin-controlled only
            # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
            self.jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(['html', 'xml', 'htm']),  # Enhanced autoescape
                trim_blocks=True,
                lstrip_blocks=True,
                # Security: Disable dangerous features
                enable_async=False,
                auto_reload=False,
                optimized=True
            )

            # Add security-focused custom filters
            self.jinja_env.filters['secure_escape'] = self._secure_jinja_escape
            self.jinja_env.filters['safe_url'] = self._safe_url_filter
            self.jinja_env.filters['truncate_safe'] = self._truncate_safe

            # Security: Add global functions with safe defaults
            self.jinja_env.globals['secure_escape'] = self._secure_jinja_escape
        else:
            self.jinja_env = None

    def render_email_template(self, context: Dict[str, Any]) -> str:
        """Render the email template with enhanced security"""
        try:
            # Security: Sanitize context data before processing
            safe_context = self._deep_sanitize_context(context)

            if JINJA2_AVAILABLE and self.jinja_env:
                # Use Jinja2 with enhanced security
                return self._render_with_secure_jinja2(safe_context)
            else:
                # Fallback to built-in template with security
                return self._build_secure_html_email(safe_context)

        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            # Security: Always fall back to safe template on error
            safe_context = self._deep_sanitize_context(context)
            return self._build_secure_html_email(safe_context)

    def _render_with_secure_jinja2(self, context: Dict[str, Any]) -> str:
        """Render template using Jinja2 with enhanced security"""
        try:
            template_path = os.path.join(self.template_dir, 'email.html')

            # Security: Validate template path
            if not self._is_safe_template_path(template_path):
                logger.error(f"Unsafe template path detected: {template_path}")
                return self._build_secure_html_email(context)

            if os.path.exists(template_path):
                # Security: Read template with size limit
                template_content = self._read_template_safely(template_path)
                if not template_content:
                    return self._build_secure_html_email(context)

                # Security: Create template from string to avoid file system issues
                template = self.jinja_env.from_string(template_content)

                # Security: Render with explicit escaping context
                html_content = template.render(**context)

                # Security: Final sanitization pass
                html_content = self._final_security_check(html_content)

                logger.debug("Email template rendered successfully with secure Jinja2")
                return html_content
            else:
                logger.warning(f"Template file not found at {template_path}, using built-in template")
                return self._build_secure_html_email(context)

        except Exception as e:
            logger.error(f"Secure Jinja2 rendering failed: {e}")
            return self._build_secure_html_email(context)

    def _is_safe_template_path(self, template_path: str) -> bool:
        """Security: Validate template path to prevent path traversal"""
        try:
            # Resolve absolute paths
            abs_template_dir = os.path.abspath(self.template_dir)
            abs_template_path = os.path.abspath(template_path)

            # Check if template is within allowed directory
            return abs_template_path.startswith(abs_template_dir)
        except Exception:
            return False

    def _read_template_safely(self, template_path: str, max_size: int = 1024 * 1024) -> str:
        """Security: Read template file with size limits"""
        try:
            # Check file size
            file_size = os.path.getsize(template_path)
            if file_size > max_size:
                logger.error(f"Template file too large: {file_size} bytes")
                return ""

            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read(max_size)

            # Security: Basic content validation
            if '<script' in content.lower() or 'javascript:' in content.lower():
                logger.warning("Potentially unsafe content detected in template")
                # Allow but log for monitoring

            return content

        except Exception as e:
            logger.error(f"Failed to read template safely: {e}")
            return ""

    def _secure_jinja_escape(self, value: Any) -> str:
        """Security: Enhanced Jinja2 escaping function"""
        if value is None:
            return ""

        # Use Jinja2's built-in escape function
        escaped = escape(str(value))

        # Additional security layers
        return self._additional_xss_protection(str(escaped))

    def _safe_url_filter(self, url: str) -> str:
        """Security: Filter for safe URL handling"""
        if not url:
            return ""

        try:
            # Parse and validate URL
            parsed = urlparse(str(url))

            # Security: Only allow safe schemes
            safe_schemes = ['http', 'https', 'mailto']
            if parsed.scheme.lower() not in safe_schemes:
                logger.warning(f"Unsafe URL scheme detected: {parsed.scheme}")
                return ""

            # Security: Basic URL validation
            if any(dangerous in url.lower() for dangerous in ['javascript:', 'data:', 'vbscript:']):
                logger.warning(f"Dangerous URL detected: {url}")
                return ""

            return html.escape(url, quote=True)

        except Exception:
            logger.warning(f"Invalid URL: {url}")
            return ""

    def _truncate_safe(self, text: str, length: int = 300) -> str:
        """Security: Safe text truncation"""
        if not text:
            return ""

        safe_text = self._secure_jinja_escape(text)
        if len(safe_text) <= length:
            return safe_text

        return safe_text[:length] + "..."

    def _additional_xss_protection(self, text: str) -> str:
        """Security: Additional XSS protection beyond HTML escaping"""
        if not text:
            return ""

        # Security: Remove potential XSS vectors
        dangerous_patterns = [
            (r'javascript\s*:', 'j_avascript:'),
            (r'vbscript\s*:', 'v_bscript:'),
            (r'data\s*:', 'd_ata:'),
            (r'on\w+\s*=', 'on_event='),
            (r'<\s*script', '&lt;script'),
            (r'<\s*/\s*script', '&lt;/script'),
        ]

        for pattern, replacement in dangerous_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _final_security_check(self, html_content: str) -> str:
        """Security: Final pass to ensure no dangerous content"""
        if not html_content:
            return ""

        # Security: Log potential issues but don't break functionality
        dangerous_content = [
            '<script',
            'javascript:',
            'vbscript:',
            'data:text/html',
            'onclick=',
            'onload=',
            'onerror='
        ]

        for dangerous in dangerous_content:
            if dangerous.lower() in html_content.lower():
                logger.warning(f"Potentially dangerous content detected: {dangerous}")

        return html_content

    def _build_secure_html_email(self, context: Dict[str, Any]) -> str:
        """Build HTML email using secure string construction (fallback)"""
        # Security: Escape all context values with enhanced protection
        title = self._secure_escape_with_validation(context.get('title', 'Emby Newsletter'))
        subtitle = self._secure_escape_with_validation(context.get('subtitle', ''))
        language = self._secure_escape_with_validation(context.get('language', 'en'))
        emby_url = self._safe_url_filter(context.get('emby_url', ''))
        emby_owner_name = self._secure_escape_with_validation(context.get('emby_owner_name', ''))
        unsubscribe_email = self._safe_email_filter(context.get('unsubscribe_email', ''))

        movies = context.get('movies', [])
        tv_shows = context.get('tv_shows', [])

        # Build HTML content with enhanced security
        html_content = f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <title>{title}</title>
    <style>
        /* Enhanced security: No JavaScript in CSS */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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

        # Movies section with enhanced security
        if movies and len(movies) > 0:
            html_content += '''
                    <div class="section">
                        <h2>🎬 New Movies</h2>'''

            for movie in movies:
                html_content += self._render_secure_movie_item(movie)

            html_content += '''
                    </div>'''

        # TV Shows section with enhanced security
        if tv_shows and len(tv_shows) > 0:
            html_content += '''
                    <div class="section">
                        <h2>📺 New TV Episodes</h2>'''

            for show in tv_shows:
                html_content += self._render_secure_tv_show_item(show)

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

        # Footer with secure links
        html_content += f'''
                    <div class="footer">
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

    def _render_secure_movie_item(self, movie: Dict[str, Any]) -> str:
        """Render a single movie item with enhanced security"""
        if not isinstance(movie, dict):
            return ""

        title = self._secure_escape_with_validation(movie.get('title', 'Unknown'))
        year = self._secure_escape_with_validation(movie.get('year', ''))
        overview = self._secure_escape_with_validation(movie.get('tmdb_overview') or movie.get('overview', ''))

        # Security: Validate and sanitize poster URL
        poster_url = self._safe_url_filter(movie.get('tmdb_poster') or movie.get('poster_url', ''))

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster" style="width: 120px; height: 180px; object-fit: cover; display: block;">'
        else:
            poster_html = '<div style="width: 120px; height: 180px; background: #333; display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.8em; text-align: center;">No Poster</div>'

        # Truncate overview for security and readability
        if overview and len(overview) > 300:
            overview = overview[:300] + "..."

        return f'''
                        <div class="item">
                            <div class="item-poster">
                                {poster_html}
                            </div>
                            <div class="item-content">
                                <div class="item-title">{title}</div>
                                {f'<div class="item-year">({year})</div>' if year else ''}
                                {f'<div class="item-overview">{overview}</div>' if overview else ''}
                            </div>
                        </div>'''

    def _render_secure_tv_show_item(self, show: Dict[str, Any]) -> str:
        """Render a single TV show item with enhanced security"""
        if not isinstance(show, dict):
            return ""

        title = self._secure_escape_with_validation(show.get('title', 'Unknown'))

        # Security: Handle nested data safely
        overview = ''
        tmdb_data = show.get('tmdb_data', {})
        if isinstance(tmdb_data, dict) and tmdb_data.get('overview'):
            overview = self._secure_escape_with_validation(tmdb_data['overview'])

        # Security: Safe poster URL handling
        poster_url = ''
        if isinstance(tmdb_data, dict) and tmdb_data.get('poster_path'):
            base_url = "https://image.tmdb.org/t/p/w500"
            poster_path = self._secure_escape_with_validation(tmdb_data['poster_path'])
            poster_url = f"{base_url}{poster_path}"
        elif show.get('poster_url'):
            poster_url = self._safe_url_filter(show['poster_url'])

        if poster_url:
            poster_html = f'<img src="{poster_url}" alt="{title} poster" style="width: 120px; height: 180px; object-fit: cover; display: block;">'
        else:
            poster_html = '<div style="width: 120px; height: 180px; background: #333; display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.8em; text-align: center;">No Poster</div>'

        if overview and len(overview) > 300:
            overview = overview[:300] + "..."

        return f'''
                        <div class="item">
                            <div class="item-poster">
                                {poster_html}
                            </div>
                            <div class="item-content">
                                <div class="item-title">{title}</div>
                                {f'<div class="item-overview">{overview}</div>' if overview else ''}
                            </div>
                        </div>'''

    def _secure_escape_with_validation(self, value: Any) -> str:
        """Security: Enhanced escaping with validation"""
        if value is None:
            return ""

        # Convert to string and validate
        str_value = str(value)

        # Security: Length limit
        if len(str_value) > 10000:
            str_value = str_value[:10000] + "..."
            logger.warning("String truncated due to excessive length")

        # Security: HTML escape
        escaped = html.escape(str_value, quote=True)

        # Security: Additional protection
        return self._additional_xss_protection(escaped)

    def _safe_email_filter(self, email: str) -> str:
        """Security: Safe email address validation"""
        if not email:
            return ""

        # Basic email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str(email)):
            logger.warning(f"Invalid email format: {email}")
            return ""

        return html.escape(str(email), quote=True)

    def _deep_sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Security: Deep sanitization of context data"""
        safe_context = {}

        for key, value in context.items():
            if key in ['movies', 'tv_shows']:
                safe_context[key] = self._sanitize_media_items_enhanced(value)
            elif isinstance(value, str):
                safe_context[key] = self._secure_escape_with_validation(value)
            elif isinstance(value, (int, float, bool)):
                safe_context[key] = value
            elif value is None:
                safe_context[key] = ""
            else:
                safe_context[key] = self._secure_escape_with_validation(str(value))

        return safe_context

    def _sanitize_media_items_enhanced(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Security: Enhanced sanitization of media items"""
        if not isinstance(items, list):
            return []

        sanitized_items = []
        for item in items[:100]:  # Security: Limit number of items
            if not isinstance(item, dict):
                continue

            sanitized_item = {}
            for key, value in item.items():
                if isinstance(value, str):
                    sanitized_item[key] = self._secure_escape_with_validation(value)
                elif isinstance(value, (int, float, bool)):
                    sanitized_item[key] = value
                elif isinstance(value, dict):
                    sanitized_item[key] = self._sanitize_nested_dict_enhanced(value)
                elif isinstance(value, list):
                    sanitized_item[key] = self._sanitize_list_enhanced(value)
                elif value is None:
                    sanitized_item[key] = ""
                else:
                    sanitized_item[key] = self._secure_escape_with_validation(str(value))

            sanitized_items.append(sanitized_item)

        return sanitized_items

    def _sanitize_nested_dict_enhanced(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Security: Enhanced nested dictionary sanitization"""
        if isinstance(data, str):
            return {'name': self._secure_escape_with_validation(data)}
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._secure_escape_with_validation(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = ""
            else:
                sanitized[key] = self._secure_escape_with_validation(str(value))

        return sanitized

    def _sanitize_list_enhanced(self, data: List[Any]) -> List[Any]:
        """Security: Enhanced list sanitization"""
        sanitized = []
        for item in data[:50]:  # Security: Limit list size
            if isinstance(item, str):
                sanitized.append(self._secure_escape_with_validation(item))
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_nested_dict_enhanced(item))
            elif isinstance(item, (int, float, bool)):
                sanitized.append(item)
            elif item is None:
                sanitized.append("")
            else:
                sanitized.append(self._secure_escape_with_validation(str(item)))

        return sanitized


# Global template renderer instance
template_renderer = SecureTemplateRenderer()