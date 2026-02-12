import streamlit as st

st.title("Welcome to Diggable")
st.markdown("Your one-stop platform for discovering music. If you have an account, please log in to access your personalized music recommendations and playlists. If you're new here, register and start exploring the world of music with us!")
# Show logout only if logged in
if st.session_state.get("session_id"):

    if st.button("Log Off"):

        # Clear all login session data
        for key in ["session_id", "user_id", "username", "email"]:
            st.session_state.pop(key, None)

        st.switch_page("pages/login.py")
