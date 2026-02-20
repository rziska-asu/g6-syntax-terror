import streamlit as st
from database import get_db_cursor

st.set_page_config(page_title="Saved Songs")
st.title("My Saved Songs")


user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("Please log in to view your saved songs.")
    st.stop()
with get_db_cursor() as cur:
    cur.execute(
        """
        SELECT id, artist_name, track_name, album_name, lastfm_url, itunes_url, image_url, created_at
        FROM liked_tracks
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    songs = cur.fetchall()

if not songs:
    st.info("You have not saved any songs yet.")
    st.stop()

if st.button("Clear All Songs", key="clear_all_songs"):
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM liked_tracks WHERE user_id = %s", (user_id,))
    st.success("All saved songs removed.")
    st.rerun()

for song in songs:
    st.write(f"🎵 **{song['track_name']}** — {song['artist_name']}")
    if song.get(lastfm_url := song.get("lastfm_url")):
        st.link_button("View on Last.fm", lastfm_url)
    
    if st.button("Remove", key=f"remove_{song['id']}"):
        with get_db_cursor() as cur:
            cur.execute(
                "DELETE FROM liked_tracks WHERE id = %s AND user_id = %s",
                (song["id"], user_id),
            )
        st.success("Song removed.")
        st.rerun()

    st.divider()
