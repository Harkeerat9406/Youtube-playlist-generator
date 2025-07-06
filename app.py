#BACKEND library
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import os
import json
from dotenv import load_dotenv

#GOOGLE libraries
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

app = Flask(__name__)
app.secret_key = os.getenv('flask_secret_key')


load_dotenv()


genai.configure(api_key = os.getenv("gemini_api"))
model = genai.GenerativeModel("gemini-2.0-flash")

system_msg = """SYSTEM MESSAGE:
You are an assistant that extracts structured music data from user input.
Return a JSON object with any of the following fields if available: "artist", "album", "track", "date".

Each field should be a list if multiple values are mentioned, e.g.:
{"artist": ["Karan Aujla", "Shubh"], "track": ["Song1", "Song2"]}

Do not include anything else except the JSON object in your response.

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
        response = model.generate_content(prompt)
        response_text = response.text
        data = json.loads(response_text)
        return jsonify(data)
    
    except json.JSONDecodeError:
        app.logger.error("Gemini returned non-JSON response: %s", response.text)
        return jsonify({"error": "Could not extract structured data. Try a clearer prompt."}), 500
    
    except Exception as e:
        app.logger.exception("Unexpected error during music data extraction")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/login')
def login():
    client_secrets = os.getenv('google_client_secret_json')
    flow = Flow.from_client_config(
        json.loads(client_secrets),
        scopes = ['https://www.googleapis.com/auth/youtube'],
        redirect_uri = 'https://morphify-delta.vercel.app/oauth2callback'
    )

    authorization_url, state = flow.authorization_url(
        access_type = 'offline',
        include_granted_scopes = 'true'
    )

    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    if 'state' not in session:
        return "Session expired or state not found. Please <a href='/login'>try again</a>.", 400
    state = session['state']

    client_secrets = os.getenv('google_client_secret_json')
    flow = Flow.from_client_config(
        json.loads(client_secrets),
        scopes = ['https://www.googleapis.com/auth/youtube'],
        state = state,
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

if __name__ == '__main__':
    app.run(debug = True)