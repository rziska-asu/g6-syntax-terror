import json
import mysql.connector
import streamlit as st
from authentication import is_email_valid
from database import get_db_cursor
from quiz_options import GENRES, MIN_PREFERENCES


st.set_page_config(page_title="Account Settings")
st.title("Account Settings")

# prevent access if not logged in
if "session_id" not in st.session_state:
    st.warning("To access settings, please log in.")
    st.stop()

user_id = st.session_state["user_id"]

# Edit Profile Section
st.subheader("Edit Profile")

# update username and email
curr_user = st.session_state.get("username", "")
curr_email = st.session_state.get("email", "")

with st.form("profile_settings"):
    new_user = st.text_input("Username", value=curr_user)
    new_email = st.text_input("Email", value=curr_email)

    save_btn = st.form_submit_button("Save Changes")

    if save_btn:
        if not new_user or not new_email:
            st.error("A Username and Email are required.")
        elif not is_email_valid(new_email):
            st.error("That email doesn't look valid. Please enter a proper email address.")
        else:
            try:
                with get_db_cursor() as cursor:
                    # updates table
                    query = "UPDATE users SET username = %s, email = %s WHERE id = %s"
                    cursor.execute(query, (new_user, new_email, user_id))

                    st.session_state["username"] = new_user
                    st.session_state["email"] = new_email
                    st.success("Profile updated successfully!")
            except mysql.connector.IntegrityError:
                st.error(
                    "Uh Oh! This Username or Email already exists. Please choose another."
                )
            except Exception as e:
                st.error(f"Error updating profile: {e}")

st.markdown("---")


st.subheader("Music Preferences")
st.write("Update your genre choices.")

saved_genres = []
try:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT latest_quiz FROM user_sessions WHERE user_id = %s", (user_id,)
        )
        res = cursor.fetchone()
        if res and res["latest_quiz"]:
            data = json.loads(res["latest_quiz"])
            saved_genres = data.get("genres", [])
except Exception:
    pass  

with st.form("genre_settings"):
    
    defaults = [g for g in saved_genres if g in GENRES]

    picks = st.multiselect("Select Genres", options=GENRES, default=defaults)

    save_prefs = st.form_submit_button("Update Preferences")

    if save_prefs:
        if len(picks) < MIN_PREFERENCES:
            st.error(f"Please select at least {MIN_PREFERENCES} genres.")
        else:
            try:
             
                json_data = json.dumps({"genres": picks})

                with get_db_cursor() as cursor:
                  
                    query = """
                        INSERT INTO user_sessions (user_id, latest_quiz) 
                        VALUES (%s, %s) 
                        ON DUPLICATE KEY UPDATE latest_quiz = VALUES(latest_quiz)
                    """
                    cursor.execute(query, (user_id, json_data))

                
                st.session_state["quiz_selections"] = picks
                st.success("Preferences saved successfully!")

            except Exception as e:
                st.error("Error saving preferences.")
                print(f"DEBUG ERROR: {e}")
