from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
import json

app = Flask(__name__)

SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_SEARCH_URL = 'https://api.spotify.com/v1/search'
LASTFM_API_KEY = 'LASTFM API KEY'  # Replace with your Last.fm API key

# Define global variables for Spotify client credentials
SPOTIFY_CLIENT_ID = 'SPOTIFY API CLIENT ID'  # Replace with your Spotify client ID
SPOTIFY_CLIENT_SECRET = 'SPOTIFY API SECRET KEY'  # Replace with your Spotify client secret

def get_spotify_access_token(client_id, client_secret):
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        return access_token
    else:
        print(f"Failed to obtain access token. Status code: {response.status_code}")
        return None

def read_lastfm_track(api_key, username, limit=1):
    url = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={api_key}&format=json&limit={limit}'

    try:
        response = requests.get(url)
        data = response.json()

        if 'track' in data['recenttracks'] and data['recenttracks']['track']:
            return data['recenttracks']['track'][0]
        else:
            print("No recent tracks found.")
            return None
    except Exception as e:
        print(f"Error getting track information from Last.fm: {e}")
        return None

def search_spotify_track(access_token, track_name, artist_name):
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'q': f'track:{track_name} artist:{artist_name}',
        'type': 'track'
    }

    response = requests.get(SPOTIFY_SEARCH_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('tracks', {}).get('items', [])
    else:
        print(f"Failed to search track on Spotify. Status code: {response.status_code}")
        return []

def create_output_dictionary(lastfm_track, spotify_track):
    output_dict = {
        'title': lastfm_track.get('name'),
        'artist': lastfm_track.get('artist', {}).get('#text'),
        'spotify_link': spotify_track[0]['external_urls']['spotify'] if spotify_track else None
    }
    return output_dict

@app.route('/api/search', methods=['GET'])
def search():
    access_token = get_spotify_access_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    if access_token:
        lastfm_track = read_lastfm_track(LASTFM_API_KEY, request.args.get('lastfm_username'))

        if lastfm_track:
            track_name = lastfm_track.get('name')
            artist_name = lastfm_track.get('artist', {}).get('#text')

            if track_name and artist_name:
                spotify_tracks = search_spotify_track(access_token, track_name, artist_name)

                output_dict = create_output_dictionary(lastfm_track, spotify_tracks)
                return jsonify(output_dict)
            else:
                return jsonify({'error': 'Track information incomplete'})
        else:
            return jsonify({'error': 'No recent Last.fm track found'})
    else:
        return jsonify({'error': 'Failed to obtain Spotify access token'})

if __name__ == '__main__':
    app.run(debug=True)
