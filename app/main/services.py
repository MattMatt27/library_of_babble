"""
Main Application Services

Helper functions for navigation and common tasks
"""
from flask import url_for
from flask_login import current_user


def get_user_nav_items():
    """
    Get navigation items based on user role.
    Returns list of navigation items with name, url, and active_page.
    """
    nav_items = [
        {'name': 'Home', 'url': url_for('main.home'), 'active_page': 'home'},
        {'name': 'Writing', 'url': url_for('writing.index'), 'active_page': 'writing'},
        {'name': 'Creating', 'url': url_for('main.creating'), 'active_page': 'creating'},
        {'name': 'Reading', 'url': url_for('books.reading'), 'active_page': 'reading'},
        {'name': 'Watching', 'url': url_for('watching.index'), 'active_page': 'watching'},
        {'name': 'Listening', 'url': url_for('music.index'), 'active_page': 'listening'},
        {'name': 'Collecting', 'url': url_for('collections.index'), 'active_page': 'collecting'},
        {'name': 'Pondering', 'url': url_for('artworks.pondering'), 'active_page': 'pondering'},
    ]

    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return nav_items
        elif current_user.role == 'viewer':
            return [item for item in nav_items if item['name'] not in ['Pondering', 'Collecting']]
    else:
        return [item for item in nav_items if item['name'] in ['Home', 'Reading', 'Writing', 'Creating']]
