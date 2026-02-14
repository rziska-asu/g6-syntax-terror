import os

# Use certifi's CA bundle so Last.fm API works on macOS (avoids SSL verify errors)
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import streamlit as st
import pylast
from dotenv import load_dotenv
from quiz_options import GENRES

# Load .env from project root (Streamlit may run with cwd elsewhere)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

st.title("Discover")

if not st.session_state.get("session_id"):
    st.warning("Please log in to use search.")
    st.stop()

def get_net():
    return pylast.LastFMNetwork(
        api_key=os.getenv("LASTFM_API_KEY", "").strip(),
        api_secret=os.getenv("LASTFM_API_SECRET", "").strip(),
    )

# --- Search by genre ---
st.subheader("Search by genre")
genre_options = [""] + GENRES
selected_genre = st.selectbox("Genre", options=genre_options, index=0, key="genre_select")
custom_genre = st.text_input("Or enter a genre", key="genre_custom")
genre = (custom_genre or selected_genre or "").strip()

search_genre_clicked = st.button("Search genre", key="discover_search_genre")
if search_genre_clicked and genre:
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

# --- General search (artist / album / track) ---
st.subheader("Search by term")
@st.cache_data(ttl=300)
def search(q: str):
    net = get_net()
    return (
        net.search_for_artist(q).get_next_page()[:10],
        net.search_for_album(q).get_next_page()[:10],
        net.search_for_track(q).get_next_page()[:10],
    )

q = st.text_input("Search", key="discover_q")
if st.button("Search", key="discover_search"):
    q = (q or "").strip()

    if not q:
        st.info("Enter a search term.")
    else:
        with st.spinner("Searching..."):
            try:
                artists, albums, tracks = search(q)
            except Exception:
                st.error("Search failed. Please try again.")
                artists, albums, tracks = [], [], []

        if not artists and not albums and not tracks:
            st.warning("No results found.")
        else:
            tab_a, tab_al, tab_t = st.tabs(["Artists", "Albums", "Songs"])

            with tab_a:
                if not artists:
                    st.write("No artists found.")
                else:
                    name = st.selectbox("Results", [a.name for a in artists], key="artist_pick")
                    a = next(x for x in artists if x.name == name)
                    st.subheader(a.name)
                    st.link_button("View details", a.get_url())

            with tab_al:
                if not albums:
                    st.write("No albums found.")
                else:
                    labels = [f"{x.artist.name} — {x.title}" for x in albums]
                    pick = st.selectbox("Results", labels, key="album_pick")
                    al = next(x for x in albums if f"{x.artist.name} — {x.title}" == pick)
                    st.subheader(al.title)
                    st.write(f"Artist: {al.artist.name}")
                    st.link_button("View details", al.get_url())

            with tab_t:
                if not tracks:
                    st.write("No songs found.")
                else:
                    labels = [f"{x.artist.name} — {x.title}" for x in tracks]
                    pick = st.selectbox("Results", labels, key="track_pick")
                    t = next(x for x in tracks if f"{x.artist.name} — {x.title}" == pick)
                    st.subheader(t.title)
                    st.write(f"Artist: {t.artist.name}")
                    st.link_button("View details / play (if available)", t.get_url())
