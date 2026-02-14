import os
import streamlit as st
import pylast

st.title("Discover")

if not st.session_state.get("session_id"):
    st.warning("Please log in to use search.")
    st.stop()

def get_net():
    return pylast.LastFMNetwork(
        api_key=os.getenv("LASTFM_API_KEY"),
        api_secret=os.getenv("LASTFM_API_SECRET"),
    )

@st.cache_data(ttl=300)
def search(q: str):
    net = get_net()
    return (
        net.search_for_artist(q).get_next_page()[:10],
        net.search_for_album(q).get_next_page()[:10],
        net.search_for_track(q).get_next_page()[:10],
    )

q = st.text_input("Search")
if st.button("Search"):
    q = (q or "").strip()

    if not q:
        st.info("Enter a search term.")
        st.stop()

    with st.spinner("Searching..."):
        try:
            artists, albums, tracks = search(q)
        except Exception:
            st.error("Search failed. Please try again.")
            st.stop()

    if not artists and not albums and not tracks:
        st.warning("No results found.")
        st.stop()

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

