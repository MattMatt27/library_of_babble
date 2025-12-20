"""
Page Headers Service

Provides functions to get page header configuration.
Uses caching to minimize database queries.

Headers are loaded in this order:
1. Database (primary source, editable via admin)
2. Config file (config/page_headers.json) - used for initial setup
3. None (no header for page)
"""
from app.models.page_headers import PageHeader
from app.extensions import db
import json
import os

# In-memory cache for page headers
_headers_cache = {}
_config_file_cache = None


def _load_config_file():
    """Load page headers from config/page_headers.json file."""
    global _config_file_cache

    if _config_file_cache is not None:
        return _config_file_cache

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config', 'page_headers.json'
    )

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                # Convert to dict keyed by slug
                _config_file_cache = {
                    h['slug']: h for h in data.get('headers', [])
                }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse page_headers.json: {e}")
            _config_file_cache = {}
    else:
        _config_file_cache = {}

    return _config_file_cache


def get_page_header(slug):
    """
    Get header info for a page.

    Checks in order: cache -> database -> config file

    Args:
        slug: The page slug (e.g., 'home', 'creating', 'collecting')

    Returns:
        Dict with tab_title, title, subtitle or None if not found
    """
    if not slug:
        return None

    # Check cache first
    if slug in _headers_cache:
        return _headers_cache[slug]

    # Check database
    header = PageHeader.query.filter_by(slug=slug).first()

    if header:
        result = {
            'tab_title': header.tab_title,
            'title': header.title,
            'subtitle': header.subtitle
        }
        _headers_cache[slug] = result
        return result

    # Check config file
    config = _load_config_file()
    if slug in config:
        config_header = config[slug]
        result = {
            'tab_title': config_header.get('tab_title'),
            'title': config_header.get('title'),
            'subtitle': config_header.get('subtitle')
        }
        _headers_cache[slug] = result
        return result

    # No header found
    return None


def set_page_header(slug, tab_title=None, title=None, subtitle=None):
    """
    Set or update a page header.

    Args:
        slug: The page slug
        tab_title: Browser tab title
        title: Page heading
        subtitle: Optional description

    Returns:
        The PageHeader instance
    """
    header = PageHeader.query.filter_by(slug=slug).first()

    if header:
        header.tab_title = tab_title
        header.title = title
        header.subtitle = subtitle
    else:
        header = PageHeader(
            slug=slug,
            tab_title=tab_title,
            title=title,
            subtitle=subtitle
        )
        db.session.add(header)

    db.session.commit()

    # Update cache
    _headers_cache[slug] = {
        'tab_title': tab_title,
        'title': title,
        'subtitle': subtitle
    }

    return header


def clear_headers_cache():
    """
    Clear the headers cache.

    Call this after bulk updates or when you need to force a refresh.
    """
    global _headers_cache, _config_file_cache
    _headers_cache = {}
    _config_file_cache = None
