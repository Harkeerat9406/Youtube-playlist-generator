import google.generativeai as genai
import os
# from dotenv import load_env
import json

genai.configure(api_key = os.getenv("gemini_api"))

model = genai.GenerativeModel("gemini-2.0-flash")

system_msg = "SYSTEM MESSAGE:\nYou are an assistant that extracts structured music data from user input. Given a user prompt, return a JSON object with the following fields if available: 'artist', 'album', 'track', 'date'. If any field is missing, omit it from the output. Do not include anything to the output other than the json object. For example, just return {\"artist\": value} or whatever fields are present in the user prompt\n\nUSER PROMPT:\n"
user_input = "I want to hear good songs from sicario album by shubh"

prompt = system_msg + user_input
response = model.generate_content(prompt)

response_text = response.text
data = json.loads(response_text)
print(response_text)