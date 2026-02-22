"""
Like, dislike, and skip actions for tracks. Persisted in DB for learning and recommendations.
"""
from database import get_db_cursor


def add_like(user_id: int, artist_name: str, track_name: str, lastfm_url: str = None, itunes_url: str = None, album_name: str = None, image_url: str = None) -> bool:
    """Record a like (save) for a track. Returns True if inserted, False if already liked."""
    with get_db_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO liked_tracks (user_id, artist_name, track_name, lastfm_url, itunes_url, album_name, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, artist_name, track_name, lastfm_url, itunes_url, album_name, image_url),
            )
            return True
        except Exception:
            return False  # e.g. duplicate


def add_dislike(user_id: int, artist_name: str, track_name: str, lastfm_url: str = None) -> bool:
    """Record a dislike for a track. Returns True if inserted, False if already disliked."""
    with get_db_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO disliked_tracks (user_id, artist_name, track_name, lastfm_url)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, artist_name, track_name, lastfm_url),
            )
            return True
        except Exception:
            return False


def add_skip(user_id: int, artist_name: str, track_name: str, lastfm_url: str = None) -> bool:
    """Record a skip for a track. Returns True if inserted, False if already skipped."""
    with get_db_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO skipped_tracks (user_id, artist_name, track_name, lastfm_url)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, artist_name, track_name, lastfm_url),
            )
            return True
        except Exception:
            return False


def is_liked(user_id: int, artist_name: str, track_name: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM liked_tracks WHERE user_id = %s AND artist_name = %s AND track_name = %s",
            (user_id, artist_name, track_name),
        )
        return cur.fetchone() is not None


def is_disliked(user_id: int, artist_name: str, track_name: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM disliked_tracks WHERE user_id = %s AND artist_name = %s AND track_name = %s",
            (user_id, artist_name, track_name),
        )
        return cur.fetchone() is not None


def is_skipped(user_id: int, artist_name: str, track_name: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM skipped_tracks WHERE user_id = %s AND artist_name = %s AND track_name = %s",
            (user_id, artist_name, track_name),
        )
        return cur.fetchone() is not None


def get_disliked_set(user_id: int) -> set:
    """Return set of (artist_name, track_name) tuples for use in filtering recommendations.
    Returns empty set if disliked_tracks table does not exist (e.g. migration not run yet).
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT artist_name, track_name FROM disliked_tracks WHERE user_id = %s",
                (user_id,),
            )
            return {(r["artist_name"], r["track_name"]) for r in cur.fetchall()}
    except Exception:
        return set()


def get_saved_songs(user_id: int) -> list:
    """Return list of liked/saved tracks for the user (for Saved Songs page)."""
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
        return cur.fetchall()


def remove_song(user_id: int, song_id: int) -> None:
    """Remove a saved (liked) track by id."""
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM liked_tracks WHERE id = %s AND user_id = %s", (song_id, user_id))
