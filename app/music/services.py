"""
Music/Spotify Business Logic and Helper Functions
"""
import os
import pandas as pd
import spotipy
from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyClientCredentials
from app.extensions import db
from app.music.models import Playlists

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


def generate_monthly_playlists_df():
    """
    Generate DataFrame of monthly playlists and mark them as site-approved.
    Returns DataFrame with playlist_id, playlist_name, playlist_art columns.
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
    for playlist in all_playlists:
        if any(month in playlist.name for month in month_list):
            matching_playlists.append({
                'playlist_id': playlist.id,
                'playlist_name': playlist.name,
                'playlist_art': playlist.album_art
            })
            # Mark as site-approved
            playlist.site_approved = True

    # Commit changes
    db.session.commit()

    # Return as DataFrame
    return pd.DataFrame(matching_playlists)


def select_playlist(monthly_playlists_df, search_term):
    """
    Select a specific playlist from monthly playlists based on search term.
    Returns tuple of (playlist_id, playlist_art, playlist_name) or (None, None, None)
    """
    selected_suffix = f'({search_term})'

    # Filter DataFrame based on selected suffix
    selected_playlist = monthly_playlists_df[
        monthly_playlists_df['playlist_name'].str.contains(selected_suffix, na=False)
    ]

    if not selected_playlist.empty:
        playlist_id = selected_playlist.iloc[0]['playlist_id']
        playlist_art = selected_playlist.iloc[0]['playlist_art']
        playlist_name = selected_playlist.iloc[0]['playlist_name']
        return playlist_id, playlist_art, playlist_name
    else:
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
