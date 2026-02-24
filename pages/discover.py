import os

# Workaround for cert issues in some environments (like Streamlit Cloud)
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import streamlit as st
import pylast
import random
from dotenv import load_dotenv
from quiz_options import GENRES
from search_history import record_search, get_recent_searches
from track_actions import (
    add_like,
    add_dislike,
    add_skip,
    is_liked,
    is_disliked,
    is_skipped,
    get_itunes_preview_url,
)

# Load .env from project root
load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
)

st.title("Discover")

if not st.session_state.get("session_id"):
    st.warning("Please log in to use search.")
    st.stop()

user_id = st.session_state.get("user_id")


# Note: This page is a bit more complex than the others, since it has multiple search modes and needs to maintain state across interactions. We use session_state to keep track of search results and the current "pool" of
# genre tracks to show, so that when you click Like/Dislike/Skip it can replace just that
# track without losing the rest of the results or going back to the API immediately.
# The recent searches section also allows auto-running a recent search when you click it, which is stored in session_state as well.
def safe_key(s: str) -> str:

    return "".join(ch if ch.isalnum() else "_" for ch in (s or ""))[:80]


def ensure_genre_state():

    if "discover_genre_query" not in st.session_state:
        st.session_state["discover_genre_query"] = ""
    if "discover_genre_pool" not in st.session_state:
        st.session_state["discover_genre_pool"] = []
    if "discover_genre_display" not in st.session_state:
        st.session_state["discover_genre_display"] = []
    if "discover_genre_artists" not in st.session_state:
        st.session_state["discover_genre_artists"] = []

    # Preview cache (avoid repeated iTunes calls on reruns)
    if "discover_preview_cache" not in st.session_state:
        st.session_state["discover_preview_cache"] = {}


# cache preview URLs to avoid repeated API calls on reruns
def preview_cached(artist: str, track: str):

    k = f"{artist}::{track}".strip().lower()
    cached = st.session_state["discover_preview_cache"].get(k)
    if cached:
        return cached

    url = get_itunes_preview_url(artist, track)
    if url:
        st.session_state["discover_preview_cache"][k] = url
    return url


def get_net():
    return pylast.LastFMNetwork(
        api_key=os.getenv("LASTFM_API_KEY", "").strip(),
        api_secret=os.getenv("LASTFM_API_SECRET", "").strip(),
    )


# build a big pool of tracks for the genre, since Last.fm's top tracks can be a bit repetitive if you go back to the API
# on every Like/Dislike/Skip. We shuffle it so it's not always the same tracks in the same order, and then store it in session_state.
# When we need a new track to show, we take the next one from the pool. If the pool runs out, we can just stop showing new tracks
# until they do a new search.
def build_genre_pool(network, genre: str, pool_limit: int = 200):
    tag = network.get_tag(genre.lower())
    raw = tag.get_top_tracks(limit=pool_limit)

    pool = []
    for t in raw:
        item = t.item
        track_name = item.get_name()
        artist_name = item.get_artist().get_name()
        try:
            track_url = item.get_url()
        except Exception:
            track_url = None

        pool.append(
            {
                "artist": artist_name,
                "track": track_name,
                "lastfm_url": track_url,
            }
        )

    random.shuffle(pool)
    return pool


def take_next_track_from_pool():
    pool = st.session_state.get("discover_genre_pool", [])
    if not pool:
        return None
    return pool.pop(0)


def replace_track_in_display(display_index: int):
    nxt = take_next_track_from_pool()
    if nxt is None:
        try:
            st.session_state["discover_genre_display"].pop(display_index)
        except Exception:
            pass
        return

    st.session_state["discover_genre_display"][display_index] = nxt


# recent searches logic: we show a list of recent searche
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
                    "text": r["query_text"],
                }
                st.rerun()


# search by genre logic: we have a dropdown of genres but also allow freeform entry.
ensure_genre_state()

st.subheader("Search by genre")
genre_options = [""] + GENRES
selected_genre = st.selectbox(
    "Genre", options=genre_options, index=0, key="genre_select"
)
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

search_genre_clicked = st.button(
    "Search genre", key="discover_search_genre"
) or st.session_state.pop("auto_genre_search", False)

if search_genre_clicked and genre:
    st.session_state["discover_genre_query"] = genre

    if user_id:
        record_search(user_id, "genre", genre)

    api_key = os.getenv("LASTFM_API_KEY", "").strip()
    api_secret = os.getenv("LASTFM_API_SECRET", "").strip()
    if not api_key or not api_secret:
        st.error(
            "Last.fm API not configured. Add LASTFM_API_KEY and LASTFM_API_SECRET to .env"
        )
    else:
        try:
            network = get_net()

            # Build a big shuffled pool ONCE, then display first 15
            st.session_state["discover_genre_pool"] = build_genre_pool(
                network, genre, pool_limit=200
            )

            tag = network.get_tag(genre.lower())
            artists = tag.get_top_artists(limit=15)
            st.session_state["discover_genre_artists"] = [
                a.item.get_name() for a in artists
            ]

            display = []
            while len(display) < 15:
                nxt = take_next_track_from_pool()
                if not nxt:
                    break
                display.append(nxt)

            st.session_state["discover_genre_display"] = display

        except Exception as e:
            st.error("Last.fm request failed. Check the details below.")
            with st.expander("Error details (for debugging)"):
                st.code(str(e))

elif search_genre_clicked and not genre:
    st.warning("Select or enter a genre to search.")

# Render genre results if we have them (so reruns keep showing results)
if st.session_state.get("discover_genre_query") and (
    st.session_state.get("discover_genre_display")
    or st.session_state.get("discover_genre_artists")
):
    genre_q = st.session_state["discover_genre_query"]
    tracks_display = st.session_state.get("discover_genre_display", [])
    artists_display = st.session_state.get("discover_genre_artists", [])

    if not tracks_display and not artists_display:
        st.info(f'No songs or artists found for genre "{genre_q}".')
    else:
        if tracks_display:
            st.write("**Tracks**")
            for idx, row in enumerate(tracks_display):
                track_name = row["track"]
                artist_name = row["artist"]
                track_url = row.get("lastfm_url")

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{track_name}** — {artist_name}")

                    # plays previews if available, using the cached function to avoid repeated API calls on reruns
                    preview_url = preview_cached(artist_name, track_name)
                    if preview_url:
                        st.audio(preview_url)
                    else:
                        st.caption("No preview found for this track.")

                with col2:
                    if user_id:
                        liked = is_liked(user_id, artist_name, track_name)

                        k = f"{safe_key(artist_name)}_{safe_key(track_name)}_{idx}"

                        if st.button("Like", key=f"genre_like_{k}", disabled=liked):
                            if add_like(
                                user_id,
                                artist_name,
                                track_name,
                                lastfm_url=track_url,
                                itunes_url=preview_url,
                            ):
                                st.toast(f"Liked {track_name}")
                            replace_track_in_display(idx)
                            st.rerun()

                        if st.button("Dislike", key=f"genre_dislike_{k}"):
                            if add_dislike(
                                user_id,
                                artist_name,
                                track_name,
                                lastfm_url=track_url,
                                itunes_url=preview_url,
                            ):
                                st.toast(f"Disliked {track_name}")
                            replace_track_in_display(idx)
                            st.rerun()

                        if st.button("Skip", key=f"genre_skip_{k}"):
                            if add_skip(
                                user_id,
                                artist_name,
                                track_name,
                                lastfm_url=track_url,
                                itunes_url=preview_url,
                            ):
                                st.toast(f"Skipped {track_name}")
                            replace_track_in_display(idx)
                            st.rerun()

        if artists_display:
            st.write("**Artists**")
            for name in artists_display:
                st.write(f"**{name}**")


# General search login using (artist / album / track)

st.subheader("Search by term")


@st.cache_data(ttl=300)
def search_term(q: str):
    net = get_net()

    artists_raw = net.search_for_artist(q).get_next_page()[:10]
    albums_raw = net.search_for_album(q).get_next_page()[:10]

    tracks_raw = []
    if " - " in q:
        artist_name, track_name = [s.strip() for s in q.split(" - ", 1)]
        if artist_name and track_name:
            tracks_raw = net.search_for_track(artist_name, track_name).get_next_page()[
                :10
            ]
    else:
        try:
            artist_obj = net.get_artist(q)
            top_tracks = artist_obj.get_top_tracks(limit=10)
            tracks_raw = [t.item for t in top_tracks]
        except Exception:
            tracks_raw = []

    artists = [(a.name, a.get_url()) for a in artists_raw]
    albums = [(al.title, al.artist.name, al.get_url()) for al in albums_raw]
    tracks = [(t.title, t.artist.name, t.get_url()) for t in tracks_raw]

    return artists, albums, tracks


q = st.text_input("Search", key="discover_q")
term_clicked = st.button("Search", key="discover_search") or st.session_state.pop(
    "auto_term_search", False
)

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
    albums = results.get("albums", [])
    tracks = results.get("tracks", [])

    if not artists and not albums and not tracks:
        st.warning("No results found.")
    else:
        tab_a, tab_al, tab_t = st.tabs(["Artists", "Albums", "Songs"])

        with tab_a:
            if not artists:
                st.write("No artists found.")
            else:
                name = st.selectbox(
                    "Results", [a[0] for a in artists], key="artist_pick"
                )
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
                st.write("To search songs, type: **Artist - Track** (example format).")
            else:
                labels = [f"{artist} — {title}" for (title, artist, _) in tracks]
                pick = st.selectbox("Results", labels, key="track_pick")
                title = pick.split(" — ", 1)[1]
                artist = pick.split(" — ", 1)[0]
                url = next(u for (t, a, u) in tracks if t == title and a == artist)

                st.subheader(title)
                st.write(f"Artist: {artist}")
                st.link_button("View details / play (if available)", url)

                preview_url = preview_cached(artist, title)
                if preview_url:
                    st.audio(preview_url)
                else:
                    st.caption("No preview found for this track.")

                if user_id:
                    st.write("**Actions:**")
                    c1, c2, c3 = st.columns(3)

                    k = f"{safe_key(artist)}_{safe_key(title)}"

                    with c1:
                        if st.button("Like", key=f"term_like_{k}"):
                            if add_like(
                                user_id,
                                artist,
                                title,
                                lastfm_url=url,
                                itunes_url=preview_url,
                            ):
                                st.toast(f"Liked {title}")
                            st.rerun()
                    with c2:
                        if st.button("Dislike", key=f"term_dislike_{k}"):
                            if add_dislike(
                                user_id,
                                artist,
                                title,
                                lastfm_url=url,
                                itunes_url=preview_url,
                            ):
                                st.toast(f"Disliked {title}")
                            st.rerun()
                    with c3:
                        if st.button("Skip", key=f"term_skip_{k}"):
                            if add_skip(
                                user_id,
                                artist,
                                title,
                                lastfm_url=url,
                                itunes_url=preview_url,
                            ):
                                st.toast(f"Skipped {title}")
                            st.rerun()
