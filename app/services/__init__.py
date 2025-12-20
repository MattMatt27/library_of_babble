"""
App-level Services

Services that apply across the entire application, not specific to any blueprint.
"""
from app.services.settings import get_setting, set_setting, clear_settings_cache
from app.services.page_headers import get_page_header, set_page_header, clear_headers_cache

__all__ = [
    'get_setting',
    'set_setting',
    'clear_settings_cache',
    'get_page_header',
    'set_page_header',
    'clear_headers_cache',
]
