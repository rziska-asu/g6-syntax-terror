import streamlit as st
import pylast
import os
import random
from dotenv import load_dotenv


from track_actions import (
    is_liked,
    add_like,
    get_disliked_set,
    is_disliked,
    add_dislike,
    is_skipped,
    add_skip,
    get_itunes_preview_url,
)

# Use env for API keys when available
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET")

network = pylast.LastFMNetwork(
    api_key=LASTFM_API_KEY,
    api_secret=LASTFM_API_SECRET,
)


def norm_key(artist: str, track: str) -> str:
    return f"{artist.strip().lower()}::{track.strip().lower()}"


def ensure_state():
    if "rec_pool" not in st.session_state:
        st.session_state["rec_pool"] = []

    if "rec_tracks" not in st.session_state:
        st.session_state["rec_tracks"] = []

    if "rec_genre" not in st.session_state:
        st.session_state["rec_genre"] = None

    # prevents song from showing up again in the same session after being liked/disliked/skipped
    if "rec_seen" not in st.session_state:
        st.session_state["rec_seen"] = set()

    # Cache iTunes previews to avoid redundant API calls and speed up the UI
    if "preview_cache" not in st.session_state:
        st.session_state["preview_cache"] = {}

    if "rec_source_genre" not in st.session_state:
        st.session_state["rec_source_genre"] = None

# functions to build and manage the recommendation pool based on genre and user preferences, ensuring disliked tracks are filtered out and seen tracks aren't repeated in the same session
def build_pool_for_genre(genre: str, user_id: int, pool_limit: int = 200):
    tag = network.get_tag(genre.lower())
    raw = tag.get_top_tracks(limit=pool_limit)

    disliked_set = get_disliked_set(user_id)

    pool = []
    for t in raw:
        item = t.item
        track_name = item.get_name()
        artist_name = item.get_artist().get_name()

        if (artist_name, track_name) in disliked_set:
            continue

        k = norm_key(artist_name, track_name)
        if k in st.session_state["rec_seen"]:
            continue

        try:
            track_url = item.get_url()
        except Exception:
            track_url = None

        pool.append(
            {"artist": artist_name, "track": track_name, "lastfm_url": track_url}
        )

    random.shuffle(pool)
    return pool

# functions to manage the recommendation pool and track list, replacing tracks when liked/disliked/skipped, and fetching preview URLs with caching to optimize performance
def refill_tracks_if_needed(genre: str, user_id: int, display_count: int = 10):
    ensure_state()

    genre_changed = st.session_state["rec_genre"] != genre

    if genre_changed:
        st.session_state["rec_genre"] = genre
        st.session_state["rec_pool"] = build_pool_for_genre(
            genre, user_id, pool_limit=200
        )
        st.session_state["rec_tracks"] = []

    while len(st.session_state["rec_tracks"]) < display_count:
        if not st.session_state["rec_pool"]:
            st.session_state["rec_pool"] = build_pool_for_genre(
                genre, user_id, pool_limit=200
            )
            if not st.session_state["rec_pool"]:
                break

        nxt = st.session_state["rec_pool"].pop(0)
        st.session_state["rec_tracks"].append(nxt)
        st.session_state["rec_seen"].add(norm_key(nxt["artist"], nxt["track"]))


def replace_one_track_at_index(index: int, genre: str, user_id: int):
    ensure_state()

    if index < 0 or index >= len(st.session_state["rec_tracks"]):
        return

    if not st.session_state["rec_pool"]:
        st.session_state["rec_pool"] = build_pool_for_genre(
            genre, user_id, pool_limit=200
        )

    if not st.session_state["rec_pool"]:
        return

    nxt = st.session_state["rec_pool"].pop(0)
    st.session_state["rec_tracks"][index] = nxt
    st.session_state["rec_seen"].add(norm_key(nxt["artist"], nxt["track"]))


def get_preview_cached(artist: str, track: str):
    """
    Get iTunes preview URL with caching to minimize API calls. 
    """
    ensure_state()
    k = norm_key(artist, track)

    cached = st.session_state["preview_cache"].get(k)
    if cached:
        return cached

    url = get_itunes_preview_url(artist, track)

    if url:
        st.session_state["preview_cache"][k] = url

    return url


# Page UI and interactions
st.title("Based on your music preferences, here are some tracks you might like!")

user_id = st.session_state.get("user_id")
if not user_id:
    st.info("Please log in to see recommendations.")
    st.stop()

ensure_state()

prefs = st.session_state.get("quiz_selections", [])
if not prefs:
    st.warning(
        "No music preferences found. Go to Account Settings and select your genres."
    )
    st.stop()

if not st.session_state["rec_source_genre"]:
    st.session_state["rec_source_genre"] = random.choice(prefs)

current_genre = st.session_state["rec_source_genre"]

# Shows genres
st.caption(f"Generating recommendations for: **{current_genre}**")


if st.button("Recommend More"):
    st.session_state["rec_pool"] = []
    st.session_state["rec_tracks"] = []
    st.session_state["rec_genre"] = None

    if prefs:
        st.session_state["rec_source_genre"] = random.choice(prefs)

    st.rerun()

refill_tracks_if_needed(current_genre, user_id, display_count=10)

tracks_list = st.session_state["rec_tracks"]
if not tracks_list:
    st.write("No recommendations found right now. Try Recommend More.")
    st.stop()

for i, track_data in enumerate(list(tracks_list)):
    artist_name = track_data["artist"]
    track_name = track_data["track"]
    track_url = track_data.get("lastfm_url")

    st.subheader(f"{track_name}")
    st.write(f"by **{artist_name}**")

    preview_url = get_preview_cached(artist_name, track_name)
    if preview_url:
        st.audio(preview_url)  # don't force format
    else:
        st.caption("No preview found for this track.")

    col1, col2, col3, col4 = st.columns(4)
    k = norm_key(artist_name, track_name)

    with col1:
        like_disabled = is_liked(user_id, artist_name, track_name)
        if st.button("Like (Save)", key=f"like_{i}_{k}", disabled=like_disabled):
            add_like(
                user_id,
                artist_name,
                track_name,
                lastfm_url=track_url,
                itunes_url=preview_url,
            )
            st.toast("Saved!")
            replace_one_track_at_index(i, current_genre, user_id)
            st.rerun()

    with col2:
        dislike_disabled = is_disliked(user_id, artist_name, track_name)
        if st.button("Dislike", key=f"dislike_{i}_{k}", disabled=dislike_disabled):
            add_dislike(
                user_id,
                artist_name,
                track_name,
                lastfm_url=track_url,
                itunes_url=preview_url,
            )
            st.toast("Disliked.")
            replace_one_track_at_index(i, current_genre, user_id)
            st.rerun()

    with col3:
        skip_disabled = is_skipped(user_id, artist_name, track_name)
        if st.button("Skip", key=f"skip_{i}_{k}", disabled=skip_disabled):
            add_skip(
                user_id,
                artist_name,
                track_name,
                lastfm_url=track_url,
                itunes_url=preview_url,
            )
            st.toast("Skipped.")
            replace_one_track_at_index(i, current_genre, user_id)
            st.rerun()

    with col4:
        if track_url:
            st.link_button("Last.fm", track_url)
        else:
            st.button("Last.fm", disabled=True)

    st.divider()
