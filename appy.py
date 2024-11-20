from flask import Flask, request, redirect, session, url_for, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import numpy as np
import pandas as pd
import random

#╭────── · · ୨୧ · · ──────╮
#╰┈➤SPOTIFY CREDINTALS (i cant spell and i refuse to learn how)
#  ╰┈➤these are provided by spotify when the api connects (i think)
SPOTIPY_CLIENT_ID = '4391265fa4874062b36969cdd539d1c6'                    #this is the unique 'username' spotify will give our app
SPOTIPY_CLIENT_SECRET = 'fad546cc0ec2409b8a6108c7c8f9ac44'            #this is the unique 'password' spotify will give our app
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback' #this is the location that spotify will send the user after they login
#╰────── · · ୨୧ · · ──────╯

#╭────── · · ୨୧ · · ──────╮
#╰┈➤PERMISSIONS FROM USER
#  ╰┈➤these are all of the permissions we want access to
#      ╰┈➤ user-library-read: allows app to read user's library
#      ╰┈➤ user-read-private: allows app to read in profile information ( display name, profile pictures, etc. )
#      ╰┈➤ playlist-read-private: allows app to read private playlists
#      ╰┈➤ playlist-read-collaborative: allows app to read playlists that are public and collaborative
#          ╰┈➤ might not need this? - i think we do need this
SCOPE = 'user-library-read user-read-private playlist-read-private playlist-read-collaborative'
#╰────── · · ୨୧ · · ──────╯

#╭────── · · ୨୧ · · ──────╮
#╰┈➤CREATE INSTANCE OF THE FLASK SERVER
app = Flask( __name__ )               #creating an instance of the flask class | assign it to 'app' var 
                                    #__name__ = name of file, knows what to host && "templates, static files, and other resources in your project.""
app.secret_key = 'your_secret_key'  #key for management session (idk what this means tbh i just know its important)
#╰────── · · ୨୧ · · ──────╯

#╭────── · · ୨୧ · · ──────╮
#╰┈➤CREATING INSTANCE OF OAUTH
#  ╰┈➤SpotifyOAuth: class that can be found in the spotify library
sp_oauth = SpotifyOAuth( client_id=SPOTIPY_CLIENT_ID,
                         client_secret=SPOTIPY_CLIENT_SECRET,
                         redirect_uri=SPOTIPY_REDIRECT_URI,
                         scope=SCOPE )
#╰────── · · ୨୧ · · ──────╯

#╭────── · · ୨୧ · · ──────╮
#╰┈➤DISPLAYS HOME SCREEN
@app.route( '/' )
def home():
    return render_template( "home.html" )

#╰┈➤LOGIN REDIRECT TO SPOTIFY
@app.route( '/login' )
def login():
    return redirect( sp_oauth.get_authorize_url() )

#╰┈➤HANDLE RESPONSE FROM SPOTIFY OAUTH
@app.route( '/callback' )
def callback():
    token_info = sp_oauth.get_access_token( request.args['code'] )
    session['token_info'] = token_info
    return redirect( url_for( 'get_playlists' ) )

def get_playlist_images(sp):
    playlist_images = {}
    user_playlists = sp.current_user_playlists()

    for playlist in user_playlists['items']:
        playlist_images[playlist['id']] = {
            'name': playlist['name'],
            'image': playlist['images'][0]['url'] if playlist['images'] else None
        }

    return playlist_images

#╰┈➤IF LOGGED IN, WE CAN READ THE PLAYLISTS. IF NOT, REDIRECT TO LOGIN PAGE
@app.route( '/playlists' )
def get_playlists():
    sp = getAPIClient()
    #setting the users current playlists
    playlists = sp.current_user_playlists()

    #it thru playlist, add all items to the playlist list
    playlist_list = []
    for item in playlists['items']:
        playlist_id = item['id']
        playlist_name = item['name']
        owner_name = item['owner']['display_name']
        #create a hyperlink for each playlist
        playlist_list.append(f'<a href="/playlist/{playlist_id}">{playlist_name}</a> - {owner_name}')

    #this should combine all of the songs in the playlist into a string so we can index it and find it easily
    playlist_string = "<br>".join( playlist_list )

    playlist_images = get_playlist_images(sp)

    #this returns the string ( or it should, i fucked w it and i dont think it does that anymore )
    return render_template( "playlists.html", playlist_list=playlist_string, playlist_images=playlist_images)
#╰────── · · ୨୧ · · ──────╯

# Page for displaying information about tracks in a playlist as well as
#   getting and displaying recommended tracks based on the playlist
@app.route('/playlist/<playlist_id>')
def get_playlist_tracks(playlist_id):
    sp = getAPIClient()

    # Fetch the tracks from the specified playlist
    tracks = getAllPlaylistTracks(sp, playlist_id)

    # Get Dataframe of track metadata and audio features for all tracks in playlist
    playlist_tracks_info = big_ol_dataframe_of_track_info(sp, tracks)
    # Get HTML table representation of dataframe
    playlist_tracks_html = playlist_tracks_info.to_html(classes='table table-striped', index=False)

    # Get recommendations based on tracks in the playlist and then do the same thing
    recommended_tracks_df = big_ol_dataframe_of_track_info(sp, getRecommendations(sp, [track['id'] for track in tracks]))
    recommended_tracks_html = recommended_tracks_df.to_html(classes='table table-striped', index=False)

    # Plug tables into template page and return
    return render_template("playlistSongs.html", playlist_tracks_info=playlist_tracks_html, recommended_tracks_info=recommended_tracks_html)

# Organize relevant metadata and audio features for a track into a dict
def track_info_dict(track, features):
    return {
        'Name': track['name'],
        'Artist(s)': ", ".join(artist['name'] for artist in track['artists']),
        'Album': track['album']['name'], 
        'Acousticness': features['acousticness'],
        'Danceability': features['danceability'],
        'Duration_ms' : features['duration_ms'],
        'Energy': features['energy'],
        'Instrumentalness': features['instrumentalness'],
        'Liveness': features['liveness'],
        'Loudness': features['loudness'],
        'Speechiness': features['speechiness'],
        'Tempo': features['tempo'],
        'Valance': features['valence']
    }
    
# tracks: list of Spotify API track objects
# Gets audio features for the given tracks and returns a DataFrame containing
#   metadata and audio features for each track
def big_ol_dataframe_of_track_info(sp: spotipy.Spotify, tracks):
    features_by_id = audio_features_by_id(sp, [track['id'] for track in tracks])
    track_data = [track_info_dict(track, features_by_id[track['id']]) for track in tracks]
    return pd.DataFrame(track_data)

# Spotify API can only get 100 tracks at a time from a playlist
# This will repeatedly get 100 tracks until all playlist tracks are retrieved
def getAllPlaylistTracks(sp: spotipy.Spotify, playlist_id):
    tracks = []
    offset = 0
    total = 1
    while offset < total:
        response = sp.playlist_tracks(playlist_id, limit=100, offset=offset)
        total = response['total']
        new_tracks = [item['track'] for item in response['items']]
        tracks += new_tracks
        offset += 100
    return tracks

# Uses the Spotify Web API to get recommendations based on provided tracks.
# The API endpoint can only use at most 5 seed tracks, so if more than 5 are
#   provided, this generates n random samples of 5 track ids and gets one
#   recommendation for each sample.
def getRecommendations(sp: spotipy.Spotify, track_ids, n=10):
    if len(track_ids) <= 5:
        return sp.recommendations(seed_tracks=track_ids, limit=n)['tracks']
    else:
        recs = []
        for i in range(n):
            seed_track_ids = random.sample(track_ids, 5)
            recs += sp.recommendations(seed_tracks=seed_track_ids, limit=1)['tracks']
        return recs

# Gets Spotify's estimated audio feature values for the track IDs
# Returns as a dict of feature objects keyed on track id
def audio_features_by_id(sp: spotipy.Spotify, track_ids):
    features = []
    for i in range(0, len(track_ids), 100):
        features += sp.audio_features(track_ids[i:i+100])
    return {track_ids[i]: features[i] for i in range(len(track_ids))}
    
# Gets an instance of the Spotify API client
def getAPIClient():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))

    return spotipy.Spotify(auth=token_info['access_token'])

#idk what this is doing but it makes it work so
if __name__ == '__main__':
    app.run( debug = True )

from flask import Flask, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)

# Spotify API credentials
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'

# Authenticate with Spotify
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
spotify = Spotify(auth_manager=auth_manager)

# Function to get playlist names and images

