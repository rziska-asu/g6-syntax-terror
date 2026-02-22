# Based on the user's genre preferences, recommend the app reads the user's saved genre preferences.
# Recommendations load when the user opens the page or clicks "Recommend More". 10 recommendations, randomized.
# User can like (save), dislike, or skip tracks; actions persist and can influence future recommendations.

import streamlit as st
import pylast
import json
import random
import requests
from database import get_db_cursor
from track_actions import add_like, add_dislike, add_skip, is_liked, get_disliked_set

st.set_page_config(page_title="Recommendations")
st.title("Based on Your Preferences Here are Some Recommendations for You!")

# Use env for API keys when available
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
API_KEY = os.getenv("LASTFM_API_KEY", "2d574e647b2dca1dafc48f3b7a82d900").strip()
API_SECRET = os.getenv("LASTFM_API_SECRET", "2ce19faccfcf209c0319b38ea48b5244").strip()


def get_itunes_preview(artist, track_name):
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": f"{artist} {track_name}", "media": "music", "entity": "song", "limit": 1}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data["resultCount"] > 0:
            return data["results"][0].get("previewUrl")
    except Exception:
        pass
    return None


if "user_id" not in st.session_state:
    st.warning("Please log in to see your recommendations.")
    st.stop()

user_id = st.session_state["user_id"]

genres = []
try:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT latest_quiz FROM user_sessions WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if row and row["latest_quiz"]:
            data = json.loads(row["latest_quiz"])
            genres = data.get("genres", [])
except Exception:
    st.error("Error loading preferences.")

if not genres:
    st.info("Set your genre preferences in Account settings to get recommendations.")
    st.stop()

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

recommend_more = st.button("Recommend More")
if recommend_more:
    st.session_state.pop("rec_genre", None)
    st.session_state.pop("rec_tracks", None)

# Pick a genre (random or from session)
current_genre = st.session_state.get("rec_genre")
if not current_genre or recommend_more:
    current_genre = random.choice(genres)
    st.session_state["rec_genre"] = current_genre

st.subheader(f"Genre: {current_genre}")

try:
    tag = network.get_tag(current_genre.lower())
    tracks_raw = tag.get_top_tracks(limit=15)
    disliked = get_disliked_set(user_id)
    # Filter out disliked tracks so recommendations improve
    tracks_list = [t for t in tracks_raw if (t.item.get_artist().get_name(), t.item.get_name()) not in disliked]
    random.shuffle(tracks_list)
    tracks_list = tracks_list[:10]

    if not tracks_list:
        st.warning("No tracks found for this genre.")
    else:
        for t in tracks_list:
            item = t.item
            track_name = item.get_name()
            artist_name = item.get_artist().get_name()
            try:
                track_url = item.get_url()
            except Exception:
                track_url = None

            with st.container():
                st.write(f"**{track_name}** — {artist_name}")
                preview = get_itunes_preview(artist_name, track_name)
                if preview:
                    st.audio(preview, format="audio/m4a")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("Like (Save)", key=f"rec_like_{artist_name}_{track_name}", disabled=is_liked(user_id, artist_name, track_name)):
                        if add_like(user_id, artist_name, track_name, lastfm_url=track_url):
                            st.toast(f"Liked {track_name}")
                        st.rerun()
                with col2:
                    if st.button("Dislike", key=f"rec_dislike_{artist_name}_{track_name}"):
                        add_dislike(user_id, artist_name, track_name, lastfm_url=track_url)
                        st.toast(f"Disliked {track_name}")
                        st.rerun()
                with col3:
                    if st.button("Skip", key=f"rec_skip_{artist_name}_{track_name}"):
                        add_skip(user_id, artist_name, track_name, lastfm_url=track_url)
                        st.toast(f"Skipped {track_name}")
                        st.rerun()
                with col4:
                    if track_url:
                        st.link_button("Last.fm", track_url)
                st.divider()

        st.success("Don't like these? Click 'Recommend More' to try another genre!")

except Exception as e:
    st.error("Could not fetch recommendations.")
    with st.expander("Error details"):
        st.code(str(e))
