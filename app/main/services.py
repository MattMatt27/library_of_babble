"""
Main Application Services

Helper functions for navigation and common tasks
"""
from flask import url_for
from flask_login import current_user
import json
from pathlib import Path


def load_page_permissions():
    """Load page permissions from config file"""
    config_path = Path('config/page_permissions.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to default permissions if file doesn't exist
        return {'pages': []}


def is_page_visible(page_name, user_role=None):
    """
    Check if a page should be visible to a user with the given role

    Args:
        page_name: Name of the page (e.g., 'reading', 'watching')
        user_role: User role ('admin', 'user', 'viewer', or None for public)

    Returns:
        Boolean indicating if page should be visible
    """
    permissions = load_page_permissions()

    # Find the page in permissions
    for page in permissions.get('pages', []):
        if page['page_name'] == page_name:
            # Check visibility based on role
            if user_role == 'admin':
                return page.get('admin', True)
            elif user_role == 'user':
                return page.get('user', False)
            elif user_role == 'viewer':
                return page.get('viewer', False)
            else:
                # Public (not logged in)
                return page.get('public', False)

    # If page not found in config, default to admin-only for safety
    return user_role == 'admin'


def get_user_nav_items():
    """
    Get navigation items based on user role using page permissions config.
    Returns list of navigation items with name, url, and active_page.
    """
    permissions = load_page_permissions()
    user_role = current_user.role if current_user.is_authenticated else None

    nav_items = []

    for page in permissions.get('pages', []):
        # Check if this page should be visible to the current user
        if is_page_visible(page['page_name'], user_role):
            nav_items.append({
                'name': page['display_name'],
                'url': url_for(page['route_name']),
                'active_page': page['page_name']
            })

    return nav_items
