# Based on the user's genre preferences, recommend the app reads the user’s saved genre preferences.
# The app shows a list of recommended songs or artists from related genres.
# Recommendations load successfully when the user opens the recommendations page or clicks a button.
# 10 recommendations are shown and randomnize each time.
# user can save songs and saved songs are stored and can be shown in the saved_songs.py

import streamlit as st
import pylast
import json
import random
import requests
from database import get_db_cursor

st.set_page_config(page_title="recommendations")
st.title("Based on Your Preferences Here are Some Recommendations for You!")

# --- API KEYS (PASTE YOURS HERE) ---
API_KEY = "2d574e647b2dca1dafc48f3b7a82d900" 

API_SECRET = "2ce19faccfcf209c0319b38ea48b5244"


# --- HELPER: ITUNES PREVIEW ---
# (We reuse this from discover.py so the user can hear the songs)
def get_itunes_preview(artist, track_name):
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": f"{artist} {track_name}", "media": "music", "entity": "song", "limit": 1}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data["resultCount"] > 0:
            return data["results"][0].get("previewUrl")
    except:
        return None
    return None

# sets up lastfm connection 
network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

# Check Login before use
if "user_id" not in st.session_state:
    st.warning("Please log in to see your recommendations.")
    st.stop()

user_id = st.session_state["user_id"]

# grabs user's genre preferences from the MySQL database
genres = []
try:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT latest_quiz FROM user_sessions WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if row and row["latest_quiz"]:
            data = json.loads(row["latest_quiz"])
            genres = data.get("genres", [])
except Exception as e:
    st.error("Error loading preferences.")

# insert a button to trigger recommendations here (cannot test yet until we have recommendation logic)
                            
                            # Audio Preview
                            preview = get_itunes_preview(artist_name, track.title)
                            if preview:
                                st.audio(preview, format="audio/m4a")
                        
                        with col2:
                            # Save Button
                            btn_key = f"rec_{track.title}_{artist_name}"
                            if st.button("Save", key=btn_key):
                                # TODO: Database Insert Logic goes here
                                st.toast(f"Saved {track.title}!")
                                
                st.success("Don't like these? Click 'Recommend More' to try another genre!")

            except Exception as e:
                st.error("Could not fetch recommendations.")
                print(f"Rec Error: {e}")