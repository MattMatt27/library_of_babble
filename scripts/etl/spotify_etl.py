"""
Spotify Playlists ETL Script
Loads playlist data from Spotify API
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app import create_app
from app.extensions import db
from app.music.models import Playlists

# Load environment variables
load_dotenv()

# Spotify Configuration
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
username = os.getenv('SPOTIPY_USERNAME')
scope = 'playlist-read-private'
redirect_uri = 'http://localhost:8888/callback'


def parse_and_load_playlists():
    """
    Fetch and load playlists from Spotify API

    Requires Spotify API credentials in .env:
    - SPOTIPY_CLIENT_ID
    - SPOTIPY_CLIENT_SECRET
    - SPOTIPY_USERNAME
    """
    # Authorize App
    token = spotipy.util.prompt_for_user_token(username, scope, cid, secret, redirect_uri)
    sp = spotipy.Spotify(auth=token)

    counter = 0
    escape = 0
    playlists_processed = 0

    while escape < 1:
        matts_playlists = sp.current_user_playlists(1, counter)
        if matts_playlists['next'] is None:
            escape = 1
            print('Reached end of playlists')
        else:
            try:
                playlist_owner = matts_playlists['items'][0]['owner']['display_name']
                id = matts_playlists['items'][0]['id']
                name = matts_playlists['items'][0]['name']
                description = matts_playlists['items'][0]['description']
                album_art = matts_playlists['items'][0]['images'][0]['url']
                track_count = matts_playlists['items'][0]['tracks']['total']
                is_collab = matts_playlists['items'][0]['collaborative']
                is_public = matts_playlists['items'][0]['public']
            except Exception as e:
                print(f'Error parsing playlist: {e}')
                counter += 1
                continue

            data = {
                'user_id': username,
                'playlist_owner': playlist_owner,
                'id': id,
                'name': name,
                'description': description,
                'album_art': album_art,
                'track_count': track_count,
                'is_collab': is_collab,
                'is_public': is_public
            }

            existing_playlist = Playlists.query.filter_by(id=id).first()

            if existing_playlist:
                # Update existing playlist
                for key, value in data.items():
                    if key != 'site_approved':  # Preserve site_approved setting
                        setattr(existing_playlist, key, value)
                db.session.add(existing_playlist)
                print(f"Updated: {name}")
            else:
                # Create new playlist
                data['site_approved'] = 0
                record = Playlists(**data)
                db.session.add(record)
                print(f"Added: {name}")

            try:
                db.session.commit()
                playlists_processed += 1
            except Exception as e:
                db.session.rollback()
                print(f'Database error: {e}')

            counter += 1

    print(f"\nTotal playlists processed: {playlists_processed}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Spotify Playlists ETL Script")
        print("=" * 50)
        print("\nFetching playlists from Spotify API...")
        print("(You may need to authorize in your browser)\n")

        parse_and_load_playlists()

        print("\n" + "=" * 50)
        print("Spotify ETL Complete!")
