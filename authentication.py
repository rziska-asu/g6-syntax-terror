import re
import bcrypt
from database import get_db_cursor


# functions for validating password strength, hashing passwords, checking password validity, validating email format, creating users, logging in users, and fetching user information by usernames
def pw_ok(password: str) -> tuple[bool, str]:

    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Please use a password that is at least 8 characters long."
    return True, ""


def hash_pw(raw_pw: str) -> str:
    hashed = bcrypt.hashpw(raw_pw.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def is_valid_password(input_pw: str, saved_hash: str) -> bool:
    return bcrypt.checkpw(input_pw.encode("utf-8"), saved_hash.encode("utf-8"))


def is_valid_email(email: str) -> bool:

    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


# This creates a new user in the database after validating the email and password and raises errors where expected.
def create_user(username: str, email: str, password: str):
    if not is_valid_email(email):
        raise ValueError(
            "Please enter a valid email address (example: name@email.com)."
        )

    ok, msg = pw_ok(password)
    if not ok:
        raise ValueError(msg)

    hashed_pass = hash_pw(
        password
    )  # This hashes the password before storing it in the database

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """ INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) """,
                (username.strip(), email.strip().lower(), hashed_pass),
            )
    except Exception as err:

        raise ValueError(
            "Oh No! That username or email is already taken. Try another one!"
        ) from err

    return True


# Logs in a user by checking the provided email and password against the database.
def login(email: str, password: str):
    if not email or not password:
        raise ValueError("Email and password are required.")

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, username, email, password_hash
            FROM users
            WHERE email = %s
            """,
            (email.strip().lower(),),
        )
        user_row = cursor.fetchone()

    if not user_row or not is_valid_password(password, user_row["password_hash"]):
        raise ValueError("Invalid email or password.")

    return {
        "id": user_row["id"],
        "username": user_row["username"],
        "email": user_row["email"],
    }


def fetch_user_by_name(username: str):
    with get_db_cursor() as cursor:
        cursor.execute(
            """ SELECT id, username, email FROM users WHERE username = %s """,
            (username,),
        )
        return cursor.fetchone()
