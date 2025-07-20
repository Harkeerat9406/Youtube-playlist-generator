#BACKEND library
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import os
import json
from dotenv import load_dotenv
import requests
import time
from datetime import timedelta

#GOOGLE libraries
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('flask_secret_key')

app.config.update(
        SESSION_COOKIE_SECURE=True,                 # Essential for HTTPS
    SESSION_COOKIE_HTTPONLY=True,                   # Prevent XSS
    SESSION_COOKIE_SAMESITE='Lax',                  # Balance security/compatibility
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),  # Browser-side expiry
    SESSION_REFRESH_EACH_REQUEST=True               # Update expiry on each request
)


@app.before_request
def enforce_session_expiry():
    """Force clear sessions older than 1 hour"""
    CREDENTIALS_KEY = 'credentials'
    
    if CREDENTIALS_KEY in session:
        # Get last activity time (default to 0 if missing)
        last_active = session.get('session_last_active', 0)
        
        # If older than 1 hour (3600 seconds)
        if time.time() - last_active > 3600:
            session.clear()  # Nuclear option
            print("Cleared expired session")
            return
        
        # Always update activity timestamp
        session['session_last_active'] = time.time()


client_config = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": ["https://morphify-delta.vercel.app/oauth2callback"],
        "javascript_origins": ["https://morphify-delta.vercel.app"]
    }
}


genai.configure(api_key = os.getenv("gemini_api"))
model = genai.GenerativeModel("gemini-2.0-flash")

system_msg = """SYSTEM MESSAGE:
You are an assistant that extracts structured music data from user input.
Return a JSON object with any of the following fields if available: "artist", "album", "track", "date".


Separate artist with their track or album name by searching web whenever mentioned properly. For example if the prompt says "I want to hear 0 to 100 by Sidhu Moosewala and Antidote by Karan Aujla" then  
returned JSON object should be
{"track": [{"name": "0 to 100", "artist": "Sidhu Moosewala"}, {"name": "Antidote", "artist": "Karan Aujla"}]}

Do not include anything else except the JSON object in your response. There should be no extra symbols or anything.
For example if user prompt says "I want to hear No Love by shubh from Still Rollinn released in 2023", then you should only return the way JSON object is present below. ONLY THAT MUCH

{"artist": ["Shubh"], "track": ["No Love"], "album": ["Still Rollin"], "date": ["2023"]}

USER PROMPT:
"""


@app.route('/')
def home():
    return render_template('index.html')



@app.route('/is_logged_in')
def is_logged_in():
    return jsonify({'logged_in': 'credentials' in session})



@app.route('/extract_music_data', methods = ['POST'])
def extract_music_data():
    if 'credentials' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    req_data = request.get_json()
    user_input = req_data.get("prompt", "")
    prompt = system_msg + user_input

    try:
        #Step 1: Call gemini to extract structured music info
        response = model.generate_content(prompt)
        response_text = response.text
        data = json.loads(response_text)

        # Step 2: Create search queries based on available data
        search_queries = generate_search_queries(data)

        # Step 3: Create playlist
        access_token = session.get('credentials', {}).get('token')
        playlist_title = generate_playlist_title(data)
        playlist_id = create_youtube_playlist(access_token, playlist_title)        

        if not playlist_id:
            return jsonify({'error': 'Failed to create playlist on Youtube'}), 500
        
        # Step 4: Seach and add videos
        added_videos = 0
        for query in search_queries:
            video_ids = search_youtube_videos(access_token, query)
            for video_id in video_ids:
                if add_video_to_playlist(access_token, playlist_id, video_id):
                    added_videos += 1
                if added_videos >= 50:
                    break
            if added_videos >= 50:
                break
        # data['playlist_id'] = playlist_id

        return jsonify({
            'playlist_id' : playlist_id,
            'videos_added' : added_videos,
            'search_queries' : search_queries
        })
    
    except json.JSONDecodeError:
        app.logger.error("Gemini returned non-JSON response: %s", response.text)
        return jsonify({"error": "Could not extract structured data. Try a clearer prompt."}), 500
    
    except Exception as e:
        app.logger.exception("Unexpected error during music data extraction: {e}")
        return jsonify({"error": "Internal server error"}), 500



def generate_search_queries(data):
    """Generate YouTube search queries based on extracted data"""
    queries = []
    
    # 1. Specific tracks (highest priority)
    if data.get('track'):
        for item in data['track']:
            if isinstance(item, dict):  # Paired track-artist
                queries.append(f"{item['name']} {item['artist']} official")
            else:  # Unpaired track
                if data.get('artist'):   #Use first artist if available
                    queries.append(f"{item}  {data['artist'][0]} official")
                else:
                    queries.append(f"{item} official music")

    
    
    # 2. Album searches (medium priority)
    if data.get('album') and not queries:
        for album in data.get('album', []):
            # Include artist if available
            if data.get('artist'):
                for artist in data.get('artist', []):
                    queries.append(f"{album} album by {artist}")
            else:
                queries.append(f"{album} full album")
    
    # 3. Artist + year (lowest priority)
    if data.get('artist') and not queries:
        for artist in data.get('artist', []):
            if data.get('date'):
                queries.append(f"{artist} songs {data['date'][0]}")
            else:
                queries.append(f"{artist} songs")
    
    # Fallback if no specific data
    if not queries:
        queries.append("popular songs")
    
    return queries

def generate_playlist_title(data):
    """Generate appropriate playlist title based on content"""
    if data.get('track'):
        if len(data['track']) > 1:
            return f"{len(data['track'])} Selected Tracks"
        return f"{data['track'][0]}"
    
    if data.get('album'):
        if data.get('artist'):
            return f"{data['artist'][0]} - {data['album'][0]}"
        return f"{data['album'][0]} Album"
    
    if data.get('artist'):
        if data.get('date'):
            return f"{data['artist'][0]} ({data['date'][0]})"
        return f"{data['artist'][0]} Mix"
    
    return "Generated Playlist"

def search_youtube_videos(access_token, query, max_results=1):
    """Search YouTube for videos matching the query"""
    url = "https://www.googleapis.com/youtube/v3/search"
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': max_results
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 401:
        new_token = refresh_google_token()
        if new_token:
            headers['Authorization'] = f'Bearer {new_token}'
            response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return [item['id']['videoId'] for item in response.json().get('items', [])]
    return []

def add_video_to_playlist(access_token, playlist_id, video_id):
    """Add a video to the specified playlist"""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    
    response = requests.post(
        url,
        headers=headers,
        json=body,
        params={'part': 'snippet'}
    )
    
    if response.status_code == 401:
        new_token = refresh_google_token()
        if new_token:
            headers['Authorization'] = f'Bearer {new_token}'
            response = requests.post(url, headers=headers, json=body, params={'part': 'snippet'})
    
    return response.status_code == 200



@app.route('/login')
def login():
    session.clear()

    flow = Flow.from_client_config(
        client_config,
        scopes = ['https://www.googleapis.com/auth/youtube'],
        redirect_uri = 'https://morphify-delta.vercel.app/oauth2callback'
    )

    authorization_url, state = flow.authorization_url(
        access_type = 'offline',
        include_granted_scopes = 'true',
        prompt='consent'        #Ensures refresh token is returned
    )

    session['state'] = state
    session['session_last_active'] = time.time()

    response= redirect(authorization_url)
    response.headers['Cache-Control'] = 'no-store, must-revalidate'
    return redirect(authorization_url)



@app.route('/oauth2callback')
def oauth2callback():
    if 'state' not in session:
        return "Session expired or state not found. Please <a href='/login'>try again</a>.", 400
    state = session['state']

    try:
        flow = Flow.from_client_config(
            client_config,
            scopes = ['https://www.googleapis.com/auth/youtube'],
            state = session['state'],
            redirect_uri = 'https://morphify-delta.vercel.app/oauth2callback'
        )

        flow.fetch_token(authorization_response = request.url)

        credentials = flow.credentials

        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        return redirect(url_for('home'))
    
    except Exception as e:
        app.logger.error(f"OAuth error: {str(e)}")
        return "Authetication failed. Please try again.", 400



def create_youtube_playlist(access_token, title, description= "Generated by Playlist Creator"):
    url = 'https://www.googleapis.com/youtube/v3/playlists'

    headers = {
        'Authorization' : f'Bearer {access_token}',
        'Accept' : 'application/json',
        'Content-Type' : 'application/json'
    }

    body = {
        'snippet': {
            'title' : title,
            'description' : description
        },
        'status': {
            'privacyStatus' : 'unlisted'
        }
    }

    params = { 'part' : 'snippet,status'}

    response = requests.post(url, headers= headers, params= params, json=body)


    if response.status_code == 401:
        new_token = refresh_google_token()
        if new_token:
            headers['Authorization'] = f'Bearer {new_token}'
            response = requests.post(url, headers=headers, params=params, json=body)
    
    if response.status_code == 200:
        playlist_data = response.json()
        return playlist_data.get('id')             #Return Playlist ID
    else:
        print("Youtube API error:", response.text)
        return None
    


def refresh_google_token():
    if 'credentials' not in session:
        return None
        
    creds = session['credentials']
    token_url = creds['token_uri']
    
    response = requests.post(
        token_url,
        data={
            'client_id': creds['client_id'],
            'client_secret': creds['client_secret'],
            'refresh_token': creds['refresh_token'],
            'grant_type': 'refresh_token'
        }
    )
    
    if response.status_code == 200:
        new_token = response.json().get('access_token')
        session['credentials']['token'] = new_token
        session.modified = True
        return new_token
    return None


if __name__ == '__main__':
    app.run(debug = True)