import spotipy
import pandas as pd
import numpy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv('ids.env')

# Matt's IDs and Configuration
cid = os.getenv('SPOTIPY_PLAYLIST_PARSE_CID')
secret = os.getenv('SPOTIPY_PLAYLIST_PARSE_SECRET') 
username = os.getenv('SPOTIPY_PLAYLIST_PARSE_USERNAME')
scope = 'playlist-read-private'
redirect_uri = 'http://localhost:8888/callback'

# Authorize App
token = spotipy.util.prompt_for_user_token(username, scope, cid, secret, redirect_uri)
sp = spotipy.Spotify(auth=token)

counter = 0
escape = 0
while escape < 1:
    matts_playlists = sp.current_user_playlists(1,counter)
    if matts_playlists['next'] is None:
        escape = 1
        print('end')
    else: 
        try:
            playlist_owner = matts_playlists['items'][0]['owner']['display_name']
            playlist_id = matts_playlists['items'][0]['id']
            playlist_name = matts_playlists['items'][0]['name']
            playlist_desc = matts_playlists['items'][0]['description']
            playlist_art = matts_playlists['items'][0]['images'][0]['url']
            track_count = matts_playlists['items'][0]['tracks']['total']
            is_collab = matts_playlists['items'][0]['collaborative']
            is_public = matts_playlists['items'][0]['public']
        except:
            print('Bad playlist')
        
        # Including user_id so we can track when people like each other's playlists.
        playlist_columns = ['user_id','playlist_owner', 'playlist_id', 'playlist_name', 'playlist_desc', 'playlist_art',
                            'track_count', 'is_collab', 'is_public']
        try: 
            staged = [[username, playlist_owner, playlist_id, playlist_name, playlist_desc, playlist_art, 
                       track_count, is_collab, is_public]]

            playlistsDF = pd.DataFrame(staged, columns=playlist_columns)
        except ValueError:
            print('ValueError: You probably have your parenthesees wrong.')
        except:
            print('UnknownError: Please write an exception case once you figure out what happened.')
        
        try:
            playlistsDF.to_csv('6-26-2024_matts_playlists.csv', index=False, mode='a',header=False)
        except PermissionError: 
            print('PermissionError: Please close the file before writing to it.')
        except:
            print('UnknownError: Please write an exception case once you figure out what happened.')
        counter += 1
