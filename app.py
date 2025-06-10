import google.generativeai as genai
from flask import Flask, jsonify, request, render_template
import os
import json
from dotenv import load_dotenv

load_dotenv()

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

if __name__ == '__main__':
    app.run(debug = True)