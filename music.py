import spotipy
import pandas as pd
import csv
import numpy
import os
import sqlite3
from datetime import datetime, timedelta
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
    
    # Define the month format used in playlist names
    month_format = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'June',
        7: 'July', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    
    # Get the current date and calculate the last completed month
    current_date = datetime.now()
    last_month = current_date.replace(day=1) - timedelta(days=1)
    
    # Generate the month_list dynamically
    start_date = datetime(2019, 2, 1)
    month_list = []
    while start_date <= last_month:
        month_str = f"({month_format[start_date.month]} {str(start_date.year)[2:]})"
        month_list.append(month_str)
        start_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1)
    
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

def get_site_approved_playlists():
    playlists = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all books
    cursor.execute('SELECT id, name, album_art, description FROM playlists WHERE site_approved = 1')
    rows = cursor.fetchall()

    for row in rows:

        playlist = {
            'id': row[0], 
            'name': row[1],
            'album_art': row[2], 
            'description': row[3]
        }
        playlists.append(playlist)

    conn.close() 

    return playlists