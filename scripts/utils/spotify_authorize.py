"""
One-time Spotify authorization helper.

Run this LOCALLY once to obtain a long-lived refresh token. Copy the
printed value into your .env file as SPOTIPY_REFRESH_TOKEN, and into
your production secret store (e.g. AWS SSM Parameter Store), so the
ETL can run silently without ever opening a browser again.

Usage:
    python scripts/utils/spotify_authorize.py

Requirements (in .env):
    SPOTIPY_CLIENT_ID
    SPOTIPY_CLIENT_SECRET
    SPOTIPY_REDIRECT_URI  (optional — defaults to http://localhost:8888/callback;
                           must match a Redirect URI configured on your Spotify
                           Developer dashboard for this app)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
# Spotify's 2025 policy rejects http://localhost as "insecure"; 127.0.0.1
# over plain HTTP is still allowed for local development.
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
SCOPE = 'playlist-read-private'


def main():
    if not (CLIENT_ID and CLIENT_SECRET):
        print("ERROR: SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    print("Spotify Authorization (one-time)")
    print("=" * 50)
    print(f"Client ID:    {CLIENT_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()
    print("Make sure the Redirect URI above is registered on your")
    print("Spotify Developer dashboard for this app, otherwise the")
    print("authorization flow will fail.")
    print()
    print("A browser window will open to authorize. After approving,")
    print("Spotify will redirect to the URI above and this script will")
    print("capture the refresh token.")
    print()

    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=True,
        cache_path=None,
    )

    # This call opens the browser, captures the code, exchanges for tokens
    token_info = auth_manager.get_access_token(as_dict=True)

    refresh_token = token_info.get('refresh_token')
    if not refresh_token:
        print("ERROR: Spotify did not return a refresh token. Try running again.")
        sys.exit(1)

    print()
    print("=" * 50)
    print("AUTHORIZED. Save this value as SPOTIPY_REFRESH_TOKEN:")
    print()
    print(f"  {refresh_token}")
    print()
    print("Add it to:")
    print("  - .env (for local development)")
    print("  - your production secret store (e.g. AWS SSM Parameter Store)")
    print()
    print("Once stored, scripts/etl/spotify_etl.py and the admin")
    print("'Refresh Spotify' button will run without further prompts.")


if __name__ == '__main__':
    main()
