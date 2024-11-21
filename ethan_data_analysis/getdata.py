import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import os

SPOTIPY_CLIENT_ID = '4391265fa4874062b36969cdd539d1c6'                    #this is the unique 'username' spotify will give our app
SPOTIPY_CLIENT_SECRET = 'fad546cc0ec2409b8a6108c7c8f9ac44'            #this is the unique 'password' spotify will give our app
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback' #this is the location that spotify will send the user after they login
SCOPE = 'user-library-read user-read-private playlist-read-private playlist-read-collaborative'

sp_oauth = SpotifyOAuth( client_id=SPOTIPY_CLIENT_ID,
                         client_secret=SPOTIPY_CLIENT_SECRET,
                         redirect_uri=SPOTIPY_REDIRECT_URI,
                         scope=SCOPE )

sp = spotipy.Spotify(auth_manager=sp_oauth)

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

playlist_id = '2witLa0lH1ObBJKvEyPkM1'
playlist_tracks = getAllPlaylistTracks(sp, playlist_id)

thisdir = os.path.dirname(os.path.realpath(__file__))
destdir = thisdir + "/data/" + playlist_id
os.makedirs(destdir, exist_ok=True)

playlist_df = big_ol_dataframe_of_track_info(sp, playlist_tracks)
playlist_df.to_csv(destdir + '/playlist.csv', index=False)

rec_df = big_ol_dataframe_of_track_info(sp, getRecommendations(sp, [track['id'] for track in playlist_tracks], 50))
rec_df.to_csv(destdir + '/recommendations.csv', index=False)
