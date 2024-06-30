import spotipy
import pandas as pd
import csv
import numpy
import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv('ids.env')

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET') 

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise ValueError("Spotify IDs are not set.")

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET))

# Function to generate monthly playlists DataFrame
def generate_monthly_playlists_df():
    monthly_playlists_df = pd.DataFrame(columns=['playlist_name', 'playlist_id', 'playlist_art'])
    month_list = ['(Feb 19)', '(Mar 19)', '(Apr 19)', '(May 19)', '(June 19)', '(July 19)', '(Aug 19)', '(Sep 19)', '(Oct 19)', '(Nov 19)', '(Dec 19)',
                  '(Jan 20)', '(Feb 20)', '(Mar 20)', '(Apr 20)', '(May 20)', '(June 20)', '(July 20)', '(Aug 20)', '(Sep 20)', '(Oct 20)', '(Nov 20)', '(Dec 20)',
                  '(Jan 21)', '(Feb 21)', '(Mar 21)', '(Apr 21)', '(May 21)', '(June 21)', '(July 21)', '(Aug 21)', '(Sep 21)', '(Oct 21)', '(Nov 21)', '(Dec 21)',
                  '(Jan 22)', '(Feb 22)', '(Mar 22)', '(Apr 22)', '(May 22)', '(June 22)', '(July 22)', '(Aug 22)', '(Sep 22)', '(Oct 22)', '(Nov 22)', '(Dec 22)',
                  '(Jan 23)', '(Feb 23)', '(Mar 23)', '(Apr 23)', '(May 23)', '(June 23)', '(July 23)', '(Aug 23)', '(Sep 23)', '(Oct 23)', '(Nov 23)', '(Dec 23)',
                  '(Jan 24)', '(Feb 24)', '(Mar 24)', '(Apr 24)', '(May 24)', '(June 24)']

    with open('data/matts_playlists.csv', 'r', encoding='iso-8859-1') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if any(month in row['playlist_name'] for month in month_list):
                monthly_playlists_df = monthly_playlists_df.append(row, ignore_index=True)
    return monthly_playlists_df

# Function to select playlist based on month and year
def select_playlist(monthly_playlists_df, search_term):
    selected_suffix = f'({search_term})'

    # Filter the DataFrame based on the selected suffix
    selected_playlist = monthly_playlists_df[monthly_playlists_df['playlist_name'].str.contains(selected_suffix)]

    if not selected_playlist.empty:
        # Get the playlist details (e.g., ID and art) from the selected row
        playlist_id = selected_playlist.iloc[0]['playlist_id']
        playlist_art = selected_playlist.iloc[0]['playlist_art']
        playlist_name = selected_playlist.iloc[0]['playlist_name']

        return playlist_id, playlist_art, playlist_name
    else:
        return None, None, None

def get_tracks_artists(playlist_id):
	playlist_tracks = spotify.playlist_tracks(playlist_id)
	track_names = [track['track']['name'] for track in playlist_tracks['items']]
	artists = [', '.join([artist['name'] for artist in track['track']['artists']]) for track in playlist_tracks['items']]
	artwork_urls = [track['track']['album']['images'][0]['url'] for track in playlist_tracks['items']]
	return track_names, artists, artwork_urls

def music_test():
	birdy_uri = 'spotify:artist:2WX2uTcsvV5OnS0inACecP'
	results = spotify.artist_albums(birdy_uri, album_type='album')
	albums = results['items']
	while results['next']:
	    results = spotify.next(results)
	    albums.extend(results['items'])

	for album in albums:
	    print(album['name'])