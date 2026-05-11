"""
Music/Playlists Routes
"""
import re
from collections import OrderedDict
from flask import render_template
from app.music import music_bp
from app.utils.security import page_visible
from app.music.services import (
    generate_monthly_playlists,
    get_site_approved_playlists,
    get_approved_playlist_collections,
)


_MONTH_TO_NUM = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'June': 6,
    'July': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}
_MONTH_PATTERN = re.compile(
    r'\((Jan|Feb|Mar|Apr|May|June|July|Aug|Sep|Oct|Nov|Dec)\s+(\d{2})\)'
)


def _organize_monthly_by_year(monthly_playlists):
    """Group monthly playlists by year, sort by month within year, years descending."""
    by_year = {}
    for p in monthly_playlists:
        match = _MONTH_PATTERN.search(p['playlist_name'])
        if not match:
            continue
        month_name = match.group(1)
        year_full = 2000 + int(match.group(2))
        month_num = _MONTH_TO_NUM[month_name]
        by_year.setdefault(year_full, []).append({
            'id': p['playlist_id'],
            'name': p['playlist_name'],
            'art': p['playlist_art'],
            'month_num': month_num,
            'month_name': month_name,
            'year': year_full,
        })
    sorted_by_year = OrderedDict()
    for year in sorted(by_year.keys(), reverse=True):
        sorted_by_year[year] = sorted(by_year[year], key=lambda x: x['month_num'])
    return sorted_by_year


@music_bp.route('/')
@page_visible('listening')
def index():
    """Listening page — playlists organized into record crates."""
    monthly_playlists = generate_monthly_playlists()
    monthly_playlist_ids = [p['playlist_id'] for p in monthly_playlists]
    monthly_by_year = _organize_monthly_by_year(monthly_playlists)

    # Get collections with playlists
    playlist_collections = get_approved_playlist_collections()

    # Get individual approved playlists (not in any collection)
    approved_playlists = get_site_approved_playlists()

    # Find which playlists are already in collections
    playlists_in_collections = set()
    for collection_data in playlist_collections.values():
        for playlist in collection_data['playlists']:
            playlists_in_collections.add(playlist['id'])

    # Filter: exclude monthly playlists AND playlists already in collections
    other_playlists = [
        playlist for playlist in approved_playlists
        if playlist['id'] not in monthly_playlist_ids
        and playlist['id'] not in playlists_in_collections
    ]

    return render_template(
        'music/index.html',
        playlist_collections=playlist_collections,
        other_playlists=other_playlists,
        monthly_by_year=monthly_by_year,
    )
