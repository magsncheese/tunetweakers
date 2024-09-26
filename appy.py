from flask import Flask, request, redirect, session, url_for, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth

#╭────── · · ୨୧ · · ──────╮
#╰┈➤SPOTIFY CREDINTALS (i cant spell and i refuse to learn how)
#  ╰┈➤these are provided by spotify when the api connects (i think)
SPOTIPY_CLIENT_ID = '67cbb4ebad8b4f23b140f6b25ba82a9a'                    #this is the unique 'username' spotify will give our app
SPOTIPY_CLIENT_SECRET = '592ab1cfd6a9498fa06825265bc0dd96'            #this is the unique 'password' spotify will give our app
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
    #getting users info
    token_info = session.get( 'token_info', None )
    if not token_info:
        return redirect( url_for( 'login' ) )

    #setting the spotify spotipy user token 
    sp = spotipy.Spotify( auth = token_info['access_token'] )
    #setting the users current playlists
    playlists = sp.current_user_playlists()
    
    #! IDK HOW TO MAKE IT SO THAT WE CAN DETERMINE WHICH PLAYLIST THEY WANT? !#
    #! MAYBE WE CAN DISPLAY EACH PLAYLIST AND THEY CLICK WHICH ONE THEY WANT? !#

    #it thru playlist, add all items to the playlist list
    playlist_list = []
    for idx, item in enumerate( playlists['items'] ):
        playlist_list.append( f"{ idx + 1 }: { item['name'] } - { item['owner']['display_name'] }" )

    #this should combine all of the songs in the playlist into a string so we can index it and find it easily
    playlist_string = "<br>".join( playlist_list )

    #this returns the string ( or it should, i fucked w it and i dont think it does that anymore )
    return render_template( "playlists.html", playlist_list=playlist_string )
#╰────── · · ୨୧ · · ──────╯

#idk what this is doing but it makes it work so
if __name__ == '__main__':
    app.run( debug = True )
