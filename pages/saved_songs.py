import streamlit as st
from track_actions import get_saved_songs, remove_song

st.set_page_config(page_title="Saved Songs")
st.title("My Saved Songs")

user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("Please log in to view your saved songs.")
    st.stop()

songs = get_saved_songs(user_id)

if not songs:
    st.info("You have not saved any songs yet. Like songs on Discover or Recommendations to see them here.")
    st.stop()

for song in songs:
    st.write(f"🎵 **{song['track_name']}** — {song['artist_name']}")
    if song.get("lastfm_url"):
        st.link_button("View on Last.fm", song["lastfm_url"])
    if st.button("Remove", key=f"remove_{song['id']}"):
        remove_song(user_id, song["id"])
        st.success("Song removed.")
        st.rerun()
    st.divider()
