from flask import Flask, request, redirect, session, url_for, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import numpy as np

#╭────── · · ୨୧ · · ──────╮
#╰┈➤SPOTIFY CREDINTALS (i cant spell and i refuse to learn how)
#  ╰┈➤these are provided by spotify when the api connects (i think)
SPOTIPY_CLIENT_ID = 'cc295554a9294e49839cdeb4e9fb812d'                    #this is the unique 'username' spotify will give our app
SPOTIPY_CLIENT_SECRET = '2344b5f0039b40489d0ceda6ba82d1ac'            #this is the unique 'password' spotify will give our app
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

    #this returns the string ( or it should, i fucked w it and i dont think it does that anymore )
    return render_template( "playlists.html", playlist_list=playlist_string )
#╰────── · · ୨୧ · · ──────╯

# Remove the duplicate route and function
@app.route('/playlist/<playlist_id>')
def get_playlist_tracks(playlist_id):
    sp = getAPIClient()
    # Fetch the tracks from the specified playlist
    tracks = sp.playlist_tracks(playlist_id)

    track_list = []

    #tracking audio features
    track_ids = []
    for item in tracks['items']:
        track = item['track']
        track_name = track['name']
        artist_names = ', '.join(artist['name'] for artist in track['artists'])
        album_name = track['album']['name']  # Get the album name
        track_id = track['id']
        
        track_list.append(f"{track_name} by {artist_names} (Album: {album_name})") 
        track_ids.append(track_id)

    #audio features for tracks
    features_data = audio_features(track_ids)

    track_list_with_features = []
    for track_id in track_ids:
        features = features_data[track_id]
        track_name = next(item['track']['name'] for item in tracks['items'] if item['track']['id'] == track_id)
        artist_names = ', '.join(artist['name'] for artist in next(item['track']['artists'] for item in tracks['items'] if item['track']['id'] == track_id))
        album_name = next(item['track']['album']['name'] for item in tracks['items'] if item['track']['id'] == track_id)
        
        track_list_with_features.append(
            f"{track_name} by {artist_names} (Album: {album_name}) "
            f"- Danceability: {features['danceability']:.2f}, Energy: {features['energy']:.2f}, Popularity: {features['popularity']}"
        )

    track_string = "<br>".join(track_list_with_features)

    recs = getRecommendations([item['track']['id'] for item in tracks['items']])

    rec_string = "<br>".join([f"{rec['name']} by {', '.join(artist['name'] for artist in rec['artists'])} (Album: {rec['album']['name']}" for rec in recs])

    return render_template("playlistSongs.html", track_list=track_string, rec_list=rec_string)

def getRecommendations(track_ids):
    sp = getAPIClient()
    recs = sp.recommendations(seed_tracks=track_ids[:4], limit=5)['tracks']
    return recs

#get some features about the songs
def audio_features(track_ids):
    sp = getAPIClient()
    features_data = {}
    
    for track_id in track_ids:
        features = sp.audio_features(track_id)[0]
        popularity = sp.track(track_id)['popularity']

        features_data[track_id] = {
            'danceability':features['danceability'],
            'energy': features['energy'],
            'popularity': popularity
        }
    return features_data

def getAPIClient():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))

    return spotipy.Spotify(auth=token_info['access_token'])

#idk what this is doing but it makes it work so
if __name__ == '__main__':
    app.run( debug = True )
