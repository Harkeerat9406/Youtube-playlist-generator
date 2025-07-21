# 🎵 AI-Powered YouTube Playlist Generator

Always wanted a ready-to-go playlist of the exact songs I like — from a specific artist, album, or year — with zero manual searching.  
So I built it!

This project is a smart web app that takes natural language prompts like  
_“Play Sidhu Moosewala’s 2023 hits + Antidote by Karan Aujla”_  
and converts them into curated, unlisted YouTube playlists on your personal account using **Gemini Pro** and the **YouTube Data API**.

---

## ⚙️ How to Use

1. First, install `pipenv` (if not already installed):

   ```bash
   pip install pipenv
   ```

2. Then install all required dependencies using:

   ```bash
   pipenv install
   ```

3. After installing, activate the environment and run the app:

   ```bash
   pipenv shell
   python app.py
   ```

---

## 🚀 Features

- 💬 Accepts natural language prompts with artist, song, album, and year filters
- 🔍 Uses Gemini Pro (via API) to extract structured data from prompts
- 🎯 Ensures accurate matches via YouTube search with smart filters (artist + "official" + year)
- 🔒 OAuth2 authentication to access the user's YouTube account
- 📁 Automatically creates unlisted playlists with official music videos only
- ♻️ Token refresh handled for uninterrupted access
- ❌ Prevents duplicate playlist creation with timestamped titles
- 🌐 Hosted securely with HTTPS support via [Vercel](https://vercel.com)

---

## 🧠 Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML + CSS + JS
- **AI**: Gemini 2.5 Pro (via Google AI Studio)
- **Auth**: Google OAuth2 (offline scope)
- **Deployment**: Vercel with Python runtime
- **YouTube Integration**: YouTube Data API v3

---

## 📚 What I Learned

- HTTPS is mandatory for Google OAuth – learned this the hard way and resolved it by deploying to Vercel.
- Gemini returns JSON in Markdown — I built a parser to clean and use it.
- YouTube’s free quota is limited — had to design efficient API usage strategies.
- Token management must be airtight — even offline tokens require secure session handling.
- Not all album queries are reliable — cross-checking metadata and fallback handling is key.

---

## ⚠️ Limitations

- 🔐 This app is not yet verified by Google — only **test users** added by the developer can access it.  
  ➕ Comment if you'd like to be added as a tester.
- 🧠 Gemini 2.5 Pro can sometimes misidentify album tracklists — album-based playlist generation may not always be perfect.
- 🚨 Free-tier YouTube Data API restricts the number of requests — bulk requests or very frequent use might hit quota limits.

---

## 🙌 Acknowledgements

Special thanks to everyone who helped test and gave feedback during development!

---

## 📎 License

This project is for educational and testing purposes only. Do not use it for commercial purposes without appropriate authorization from respective APIs and data providers.
