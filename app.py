#BACKEND library
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import os
import json
from dotenv import load_dotenv

#GOOGLE libraries
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow
import uuid

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('flask_secret_key')

genai.configure(api_key = os.getenv("gemini_api"))
model = genai.GenerativeModel("gemini-2.0-flash")

system_msg = "SYSTEM MESSAGE:\nYou are an assistant that extracts structured music data from user input. Given a user prompt, return a JSON object with the following fields if available: 'artist', 'album', 'track', 'date'. If any field is missing, omit it from the output. Do not include anything to the output other than the json object. For example, just return {\"artist\": value} or whatever fields are present in the user prompt\n\nUSER PROMPT:\n"

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/extract_music_data', methods = ['POST'])
def extract_music_data():
    req_data = request.get_json()

    user_input = req_data.get("prompt", "")

    prompt = system_msg + user_input
    response = model.generate_content(prompt)
    response_text = response.text

    data = json.loads(response_text)
    return jsonify(data)

@app.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes = ['https://www.googleapis.com/auth/youtube'],
        redirect_uri = 'http://localhost:5000/oauth2callback'
    )

    authorization_url, state = flow.authorization_url(
        access_type = 'offline',
        include_granted_scopes = 'true'
    )

    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']

    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes = ['https://www.googleapis.com/auth/youtube'],
        state = state,
        redirect_uri = 'http://localhost:5000/oauth2callback'
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