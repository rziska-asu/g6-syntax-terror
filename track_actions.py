"""
Like, dislike, and skip actions for tracks. Persisted in DB for learning and recommendations.
"""
import requests
from database import get_db_cursor


def _commit_if_possible(cur) -> None:
    """
    Some implementations of get_db_cursor auto-commit, some don't.
    This makes writes reliable without breaking autocommit setups.
    """
    try:
        cur.connection.commit()
    except Exception:
        pass


# -------------------------
# WRITE ACTIONS
# -------------------------

def add_like(
    user_id: int,
    artist_name: str,
    track_name: str,
    lastfm_url: str = None,
    itunes_url: str = None,
    album_name: str = None,
    image_url: str = None,
) -> bool:
    """Record a like (save) for a track. Returns True if inserted, False if already liked."""
    with get_db_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO liked_tracks
                    (user_id, artist_name, track_name, lastfm_url, itunes_url, album_name, image_url)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, artist_name, track_name, lastfm_url, itunes_url, album_name, image_url),
            )
            _commit_if_possible(cur)
            return True
        except Exception:
            # e.g., duplicate key / constraint violation
            return False


def add_dislike(
    user_id: int,
    artist_name: str,
    track_name: str,
    lastfm_url: str = None,
    itunes_url: str = None,
) -> bool:
    """
    Record a dislike for a track.
    Returns True if inserted, False if already disliked.
    """
    with get_db_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO disliked_tracks
                    (user_id, artist_name, track_name, lastfm_url, itunes_url)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                (user_id, artist_name, track_name, lastfm_url, itunes_url),
            )
            _commit_if_possible(cur)
            return True
        except Exception:
            return False


def add_skip(
    user_id: int,
    artist_name: str,
    track_name: str,
    lastfm_url: str = None,
    itunes_url: str = None,
) -> bool:
    """
    Record a skip for a track.
    Returns True if inserted, False if already skipped.
    """
    with get_db_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO skipped_tracks
                    (user_id, artist_name, track_name, lastfm_url, itunes_url)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                (user_id, artist_name, track_name, lastfm_url, itunes_url),
            )
            _commit_if_possible(cur)
            return True
        except Exception:
            return False


# -------------------------
# READ HELPERS (USED FOR DISABLING BUTTONS)
# -------------------------

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


# -------------------------
# SETS (FOR FILTERING RECOMMENDATIONS)
# -------------------------

def get_disliked_set(user_id: int) -> set:
    """
    Return set of (artist_name, track_name) tuples for use in filtering recommendations.
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


def get_liked_set(user_id: int) -> set:
    """
    Return set of (artist_name, track_name) tuples for filtering.
    Safe even if liked_tracks exists but is empty.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT artist_name, track_name FROM liked_tracks WHERE user_id = %s",
                (user_id,),
            )
            return {(r["artist_name"], r["track_name"]) for r in cur.fetchall()}
    except Exception:
        return set()


def get_skipped_set(user_id: int) -> set:
    """
    Return set of (artist_name, track_name) tuples for filtering.
    Returns empty set if skipped_tracks table does not exist (e.g. migration not run yet).
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT artist_name, track_name FROM skipped_tracks WHERE user_id = %s",
                (user_id,),
            )
            return {(r["artist_name"], r["track_name"]) for r in cur.fetchall()}
    except Exception:
        return set()


# -------------------------
# SAVED SONGS PAGE HELPERS
# -------------------------

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
        _commit_if_possible(cur)


def clear_all_saved_songs(user_id: int) -> None:
    """Clear all saved songs for the user."""
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM liked_tracks WHERE user_id = %s", (user_id,))
        _commit_if_possible(cur)

def get_itunes_preview_url(artist: str, track: str) -> str | None:
    """
    Uses the public iTunes Search API to find a short audio preview (usually .m4a).
    Returns a direct preview URL or None.
    """
    artist = (artist or "").strip()
    track = (track or "").strip()
    if not artist or not track:
        return None

    # iTunes search works best with "artist track"
    term = f"{artist} {track}"

    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": term,
                "media": "music",
                "entity": "song",
                "limit": 5,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None

        # Try to pick the best match:
        # 1) exact-ish artist match
        artist_l = artist.lower()
        track_l = track.lower()

        def score(r):
            a = (r.get("artistName") or "").lower()
            t = (r.get("trackName") or "").lower()
            s = 0
            if artist_l in a or a in artist_l:
                s += 2
            if track_l in t or t in track_l:
                s += 2
            return s

        results.sort(key=score, reverse=True)
        return results[0].get("previewUrl")
    except Exception:
        return None
