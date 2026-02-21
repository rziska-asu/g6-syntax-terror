import os

# Use certifi's CA bundle so Last.fm API works on macOS (avoids SSL verify errors)
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import streamlit as st
import pylast
from dotenv import load_dotenv
from quiz_options import GENRES
from search_history import record_search, get_recent_searches


# Load .env from project root (Streamlit may run with cwd elsewhere)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

st.title("Discover")

if not st.session_state.get("session_id"):
    st.warning("Please log in to use search.")
    st.stop()

user_id = st.session_state.get("user_id")

st.subheader("Recent searches")
if user_id:
    recent = get_recent_searches(user_id, limit=5)
    if not recent:
        st.caption("No recent searches yet.")
    else:
        for r in recent:
            label = f"{r['query_type']}: {r['query_text']}"
            if st.button(label, key=f"recent_{r['id']}"):
                st.session_state["run_recent_search"] = {
                    "type": r["query_type"],
                    "text": r["query_text"]
                }
                st.rerun()

def get_net():
    return pylast.LastFMNetwork(
        api_key=os.getenv("LASTFM_API_KEY", "").strip(),
        api_secret=os.getenv("LASTFM_API_SECRET", "").strip(),
    )

# Search by genre
st.subheader("Search by genre")
genre_options = [""] + GENRES
selected_genre = st.selectbox("Genre", options=genre_options, index=0, key="genre_select")
custom_genre = st.text_input("Or enter a genre", key="genre_custom")
genre = (custom_genre or selected_genre or "").strip()


# auto run recent searches
recent_click = st.session_state.pop("run_recent_search", None)
if recent_click:
    if recent_click["type"] == "genre":
        genre = recent_click["text"]
        st.session_state["auto_genre_search"] = True
    elif recent_click["type"] == "term":
        st.session_state["discover_q"] = recent_click["text"]
        st.session_state["auto_term_search"] = True


search_genre_clicked = st.button("Search genre", key="discover_search_genre") or st.session_state.pop("auto_genre_search", False)
if search_genre_clicked and genre:
    if user_id:
        record_search(user_id, "genre", genre)
        api_key = os.getenv("LASTFM_API_KEY", "").strip()
        api_secret = os.getenv("LASTFM_API_SECRET", "").strip()
    if not api_key or not api_secret:
        st.error("Last.fm API not configured. Add LASTFM_API_KEY and LASTFM_API_SECRET to .env")
    else:
        try:
            network = get_net()
            tag = network.get_tag(genre.lower())
            tracks = tag.get_top_tracks(limit=15)
            artists = tag.get_top_artists(limit=15)
            if not tracks and not artists:
                st.info(f"No songs or artists found for genre \"{genre}\".")
            else:
                if tracks:
                    st.write("**Tracks**")
                    for t in tracks:
                        item = t.item
                        st.write(f"**{item.get_name()}** — {item.get_artist().get_name()}")
                if artists:
                    st.write("**Artists**")
                    for a in artists:
                        item = a.item
                        st.write(f"**{item.get_name()}**")
        except Exception as e:
            st.error("Last.fm request failed. Check the details below.")
            with st.expander("Error details (for debugging)"):
                st.code(str(e))
            st.info(f"No songs or artists found for genre \"{genre}\".")
elif search_genre_clicked and not genre:
    st.warning("Select or enter a genre to search.")

# General search (artist / album / track)
st.subheader("Search by term")
@st.cache_data(ttl=300)
def search_term(q: str):
    net = get_net()

    artists_raw = net.search_for_artist(q).get_next_page()[:10]
    albums_raw  = net.search_for_album(q).get_next_page()[:10]

    # Track search in pylast needs 
    tracks_raw = []
    if " - " in q:
        artist_name, track_name = [s.strip() for s in q.split(" - ", 1)]
        if artist_name and track_name:
            tracks_raw = net.search_for_track(artist_name, track_name).get_next_page()[:10]

    else:
        try:
            artist_obj = net.get_artist(q)
            top_tracks = artist_obj.get_top_tracks(limit=10)
            tracks_raw = [t.item for t in top_tracks]
        except Exception:
            tracks_raw = []

    artists = [(a.name, a.get_url()) for a in artists_raw]
    albums  = [(al.title, al.artist.name, al.get_url()) for al in albums_raw]
    tracks  = [(t.title, t.artist.name, t.get_url()) for t in tracks_raw]

    return artists, albums, tracks

q = st.text_input("Search", key="discover_q")
term_clicked = st.button("Search", key="discover_search") or st.session_state.pop("auto_term_search", False)
if term_clicked:

    q_clean = (q or "").strip()
    if user_id and q_clean:
        record_search(user_id, "term", q_clean)


    if not q_clean:
        st.info("Enter a search term.")
    else:
        with st.spinner("Searching..."):
            try:
                artists, albums, tracks = search_term(q_clean)
                st.session_state["discover_results"] = {
                    "q": q_clean,
                    "artists": artists,
                    "albums": albums,
                    "tracks": tracks,
                }
            except Exception as e:
                st.error("Search failed. Check the details below.")
                with st.expander("Error details (for debugging)"):
                    st.code(str(e))
                st.session_state["discover_results"] = {
                    "q": q_clean,
                    "artists": [],
                    "albums": [],
                    "tracks": [],
                }

results = st.session_state.get("discover_results")

if results and results.get("q"):
    artists = results.get("artists", [])
    albums  = results.get("albums", [])
    tracks  = results.get("tracks", [])

    if not artists and not albums and not tracks:
        st.warning("No results found.")
    else:
        tab_a, tab_al, tab_t = st.tabs(["Artists", "Albums", "Songs"])

        with tab_a:
            if not artists:
                st.write("No artists found.")
            else:
                name = st.selectbox("Results", [a[0] for a in artists], key="artist_pick")
                url = next(u for n, u in artists if n == name)
                st.subheader(name)
                st.link_button("View details", url)

        with tab_al:
            if not albums:
                st.write("No albums found.")
            else:
                labels = [f"{artist} — {title}" for (title, artist, _) in albums]
                pick = st.selectbox("Results", labels, key="album_pick")
                title = pick.split(" — ", 1)[1]
                artist = pick.split(" — ", 1)[0]
                url = next(u for (t, a, u) in albums if t == title and a == artist)

                st.subheader(title)
                st.write(f"Artist: {artist}")
                st.link_button("View details", url)

        with tab_t:
            if not tracks:
                st.write('To search songs, type: **Artist - Track** (example format).')
            else:
                labels = [f"{artist} — {title}" for (title, artist, _) in tracks]
                pick = st.selectbox("Results", labels, key="track_pick")
                title = pick.split(" — ", 1)[1]
                artist = pick.split(" — ", 1)[0]
                url = next(u for (t, a, u) in tracks if t == title and a == artist)

                st.subheader(title)
                st.write(f"Artist: {artist}")
                st.link_button("View details / play (if available)", url)