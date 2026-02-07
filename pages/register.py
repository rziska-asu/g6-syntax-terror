import streamlit as st
from authentication import create_user, pw_ok, is_valid_email

st.title("Register with Diggable")

username = st.text_input("Username")
email = st.text_input("Email")
password = st.text_input("Password", type="password")
st.caption("Password must be at least 8 characters. Please use a strong password!")

# This handles the registration process when the user clicks the "Get To Digging!" button. 
if st.button("Get To Digging!"):
    if not username:
        st.error("A Username is required to register.")
    if not email:
        st.error("An Email is required to register.")
    if not password:
        st.error("A Password is required to register.") 
    elif not is_valid_email(email):
        st.error("Uh oh! Please enter a valid email address and Try again.")
    else:
        ok, msg = pw_ok(password)
        if not ok:
            st.error(msg)
        else:
            try:
                create_user(username, email, password)
                st.success("Account created! Go to the Login page to sign in.")
            except ValueError as e:
                st.error(str(e))

st.info("Already have an account? Go to the Login page to sign in!")
