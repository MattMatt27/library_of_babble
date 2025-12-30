"""
Site Settings Service

Provides functions to get and set site-wide configuration values.
Uses caching to minimize database queries.

Settings are loaded in this order:
1. Database (primary source, editable via admin)
2. Config file (config/site_settings.json) - used for initial setup
3. Hardcoded defaults (fallback)
"""
from app.models.site_settings import SiteSetting
from app.extensions import db
import json
import os

# In-memory cache for settings
_settings_cache = {}
_config_file_cache = None


def _load_config_file():
    """Load settings from config/site_settings.json file."""
    global _config_file_cache

    if _config_file_cache is not None:
        return _config_file_cache

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config', 'site_settings.json'
    )

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                # Convert to dict keyed by setting key
                _config_file_cache = {
                    s['key']: s for s in data.get('settings', [])
                }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse site_settings.json: {e}")
            _config_file_cache = {}
    else:
        _config_file_cache = {}

    return _config_file_cache


def get_setting(key, default=None):
    """
    Get a site setting by key with caching.

    Checks in order: cache -> database -> config file -> default

    Args:
        key: The setting key to retrieve
        default: Value to return if setting doesn't exist anywhere

    Returns:
        The setting value (parsed according to value_type) or default
    """
    # Check cache first
    if key in _settings_cache:
        return _settings_cache[key]

    # Check database
    setting = SiteSetting.query.filter_by(key=key).first()

    if setting:
        # Parse based on value_type
        if setting.value_type == 'json':
            value = json.loads(setting.value) if setting.value else default
        elif setting.value_type == 'boolean':
            value = setting.value.lower() in ('true', '1', 'yes') if setting.value else default
        elif setting.value_type == 'integer':
            value = int(setting.value) if setting.value else default
        else:
            value = setting.value

        _settings_cache[key] = value
        return value

    # Check config file
    config = _load_config_file()
    if key in config:
        config_setting = config[key]
        value = config_setting.get('value', default)
        _settings_cache[key] = value
        return value

    # Return default
    return default


def set_setting(key, value, value_type='string', description=None, user_id=None):
    """
    Set a site setting.

    Args:
        key: The setting key
        value: The value to store
        value_type: Type of value ('string', 'json', 'boolean', 'integer')
        description: Optional description of the setting
        user_id: Optional user ID who made the change

    Returns:
        The SiteSetting instance
    """
    setting = SiteSetting.query.filter_by(key=key).first()

    # Convert value to string for storage
    if value_type == 'json':
        stored_value = json.dumps(value)
    else:
        stored_value = str(value)

    if setting:
        setting.value = stored_value
        setting.value_type = value_type
        if description:
            setting.description = description
        if user_id:
            setting.updated_by = user_id
    else:
        setting = SiteSetting(
            key=key,
            value=stored_value,
            value_type=value_type,
            description=description,
            updated_by=user_id
        )
        db.session.add(setting)

    db.session.commit()

    # Update cache
    if value_type == 'json':
        _settings_cache[key] = value  # Store parsed value in cache
    elif value_type == 'boolean':
        _settings_cache[key] = stored_value.lower() in ('true', '1', 'yes')
    elif value_type == 'integer':
        _settings_cache[key] = int(stored_value)
    else:
        _settings_cache[key] = stored_value

    return setting


def clear_settings_cache():
    """
    Clear the settings cache.

    Call this after bulk updates or when you need to force a refresh.
    """
    global _settings_cache, _config_file_cache
    _settings_cache = {}
    _config_file_cache = None
