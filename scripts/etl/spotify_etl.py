"""
Spotify Playlists ETL Script

Loads playlist data from Spotify API into the playlists table.

Authentication: uses a stored refresh token (SPOTIPY_REFRESH_TOKEN env var)
to obtain fresh access tokens silently. No browser prompt is required at
run time, so this works inside containers / CI / the admin "Refresh
Spotify" button.

To obtain a refresh token the first time, run:

    python scripts/utils/spotify_authorize.py

That helper opens your browser once, you authorize, and it prints a
refresh token. Copy the value into .env (and into your production secret
store) as SPOTIPY_REFRESH_TOKEN, and then this script (and the admin
button) work indefinitely without further prompts.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from app import create_app
from app.extensions import db
from app.music.models import Playlists

# Load environment variables
load_dotenv()

# Spotify configuration
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
USERNAME = os.getenv('SPOTIPY_USERNAME')  # only used to tag rows in the DB
# Spotify's 2025 policy rejects http://localhost as "insecure"; 127.0.0.1
# over plain HTTP is still allowed for local development.
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
REFRESH_TOKEN = os.getenv('SPOTIPY_REFRESH_TOKEN')
SCOPE = 'playlist-read-private'


def build_spotify_client():
    """
    Construct a Spotipy client using a stored refresh token.

    Raises a clear error pointing to the authorization helper if the
    refresh token isn't set.
    """
    if not (CLIENT_ID and CLIENT_SECRET):
        raise RuntimeError(
            "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be set in the "
            "environment (e.g. .env locally, Parameter Store in production)."
        )

    if not REFRESH_TOKEN:
        raise RuntimeError(
            "SPOTIPY_REFRESH_TOKEN is not set. Run\n"
            "    python scripts/utils/spotify_authorize.py\n"
            "locally once to obtain a refresh token, then add it to .env "
            "(and to your production secret store) as SPOTIPY_REFRESH_TOKEN."
        )

    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=False,
        cache_path=None,  # never write a cache file at runtime
    )

    # Exchange the refresh token for a fresh access token. Spotify normally
    # does not rotate refresh tokens for this scope, so the stored token
    # remains valid across calls.
    token_info = auth_manager.refresh_access_token(REFRESH_TOKEN)
    return spotipy.Spotify(auth=token_info['access_token'])


def parse_and_load_playlists():
    """Fetch all playlists owned by / followed by the authenticated user
    and upsert them into the playlists table."""
    sp = build_spotify_client()

    # Spotify returns playlists in pages of 50; iterate through them all
    counter = 0
    playlists_processed = 0
    page_size = 50

    while True:
        page = sp.current_user_playlists(limit=page_size, offset=counter)
        items = page.get('items', [])
        if not items:
            break

        for item in items:
            try:
                pid = item['id']
                name = item['name']
                description = item.get('description', '')
                images = item.get('images') or []
                album_art = images[0]['url'] if images else None
                track_count = item.get('tracks', {}).get('total', 0)
                is_collab = item.get('collaborative', False)
                is_public = item.get('public', False)
                playlist_owner = (item.get('owner') or {}).get('display_name', '')
            except Exception as e:
                print(f'Error parsing playlist: {e}')
                continue

            data = {
                'user_id': USERNAME,
                'playlist_owner': playlist_owner,
                'id': pid,
                'name': name,
                'description': description,
                'album_art': album_art,
                'track_count': track_count,
                'is_collab': is_collab,
                'is_public': is_public,
            }

            existing = Playlists.query.filter_by(id=pid).first()
            try:
                if existing:
                    for key, value in data.items():
                        if key != 'site_approved':  # preserve site_approved
                            setattr(existing, key, value)
                    db.session.add(existing)
                    db.session.commit()
                    print(f"Updated: {name}")
                else:
                    new_playlist = Playlists(**data)
                    db.session.add(new_playlist)
                    db.session.commit()
                    print(f"Added: {name}")
                playlists_processed += 1
            except Exception as e:
                db.session.rollback()
                print(f'Database error: {e}')

        # If we got fewer than a full page, we're done
        if len(items) < page_size:
            break
        counter += page_size

    print(f"\nTotal playlists processed: {playlists_processed}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Spotify Playlists ETL Script")
        print("=" * 50)
        print("Fetching playlists from Spotify API...")
        print()

        parse_and_load_playlists()

        print()
        print("=" * 50)
        print("Spotify ETL Complete!")
