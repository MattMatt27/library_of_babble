"""
Music/Spotify Business Logic and Helper Functions
"""
import os
import re
import spotipy
from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyClientCredentials
from app.extensions import db
from app.music.models import Playlists
from app.common.models import Collection, CollectionItem

# Initialize Spotify client
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise ValueError("Spotify credentials not set in environment variables")

spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        SPOTIPY_CLIENT_ID,
        SPOTIPY_CLIENT_SECRET
    )
)


def generate_monthly_playlists():
    """
    Generate list of monthly playlists and mark them as site-approved.
    Returns list of dicts with playlist_id, playlist_name, playlist_art keys.
    """
    # Define month format used in playlist names
    month_format = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'June',
        7: 'July', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    # Get current date and calculate last completed month
    current_date = datetime.now()
    last_month = current_date.replace(day=1) - timedelta(days=1)

    # Generate list of month strings
    start_date = datetime(2019, 2, 1)
    month_list = []
    while start_date <= last_month:
        month_str = f"({month_format[start_date.month]} {str(start_date.year)[2:]})"
        month_list.append(month_str)
        start_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    # Query playlists from database
    all_playlists = Playlists.query.all()

    # Find matching playlists
    matching_playlists = []
    matched_playlist_ids = set()

    for playlist in all_playlists:
        # Match exact pattern (Month YY) - ensure no dash/space between month and year
        matched = False
        for month in month_list:
            # Build pattern: opening paren, month name, single space, 2-digit year, closing paren
            # Extract month and year from the month string like "(Feb 19)"
            month_parts = month.strip('()').split()  # ['Feb', '19']
            if len(month_parts) == 2:
                month_name, year = month_parts
                # Match opening paren, month, single space, year, closing paren
                exact_pattern = rf'\({month_name}\s+{year}\)'
                if re.search(exact_pattern, playlist.name):
                    matching_playlists.append({
                        'playlist_id': playlist.id,
                        'playlist_name': playlist.name,
                        'playlist_art': playlist.album_art
                    })
                    # Mark as site-approved
                    playlist.site_approved = True
                    matched_playlist_ids.add(playlist.id)
                    matched = True
                    break  # Stop checking other months once we find a match

        # If playlist has a date-like pattern but didn't match, ensure it's not approved
        if not matched and playlist.id not in matched_playlist_ids:
            # Check if it looks like a date playlist (has parentheses with month name)
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for month_name in month_names:
                if f'({month_name}' in playlist.name or f'({month_name.lower()}' in playlist.name:
                    # This looks like a date playlist but didn't match our pattern
                    playlist.site_approved = False
                    break

    # Commit changes
    db.session.commit()

    return matching_playlists


def select_playlist(monthly_playlists, search_term):
    """
    Select a specific playlist from monthly playlists based on search term.
    Returns tuple of (playlist_id, playlist_art, playlist_name) or (None, None, None)
    """
    selected_suffix = f'({search_term})'

    # Find first matching playlist
    for playlist in monthly_playlists:
        if selected_suffix in playlist['playlist_name']:
            return playlist['playlist_id'], playlist['playlist_art'], playlist['playlist_name']

    return None, None, None


def get_tracks_artists(playlist_id):
    """
    Get track names, artists, and artwork URLs for a playlist using Spotify API.
    Returns tuple of (track_names, artists, artwork_urls)
    """
    playlist_tracks = spotify.playlist_tracks(playlist_id)

    track_names = [track['track']['name'] for track in playlist_tracks['items']]
    artists = [
        ', '.join([artist['name'] for artist in track['track']['artists']])
        for track in playlist_tracks['items']
    ]
    artwork_urls = [
        track['track']['album']['images'][0]['url']
        for track in playlist_tracks['items']
    ]

    return track_names, artists, artwork_urls


def get_site_approved_playlists():
    """Get all site-approved playlists from database"""
    playlists = Playlists.query.filter_by(site_approved=True).all()

    return [{
        'id': playlist.id,
        'name': playlist.name,
        'album_art': playlist.album_art,
        'description': playlist.description
    } for playlist in playlists]


def get_approved_playlist_collections():
    """
    Get all approved collections that contain playlists.
    Returns dict: {collection_name: {description, playlists: [...]}}
    """
    # Get all approved collections, ordered by sort_order
    collections = Collection.query.filter_by(site_approved=True).order_by(Collection.sort_order).all()

    result = {}
    for collection in collections:
        # Get playlist items in this collection
        playlist_items = CollectionItem.query.filter_by(
            collection_id=collection.id,
            item_type='Playlist'
        ).all()

        if not playlist_items:
            continue  # Skip collections with no playlists

        playlists = []
        for item in playlist_items:
            playlist = Playlists.query.get(item.item_id)
            if playlist:
                playlists.append({
                    'id': playlist.id,
                    'name': playlist.name,
                    'album_art': playlist.album_art,
                    'description': playlist.description
                })

        if playlists:  # Only include if we found actual playlists
            result[collection.collection_name] = {
                'description': collection.description,
                'playlists': playlists
            }

    return result
