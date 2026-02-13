from database import get_db_cursor

def save_song(user_id: int, track_name: str, artist_name: str, track_url: str):
    sql = """
        INSERT INTO saved_songs (user_id, track_name, artist_name, track_url)
        VALUES (%s, %s, %s, %s)
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, (user_id, track_name, artist_name, track_url))
        return True
    except Exception:
    
        return False

def get_saved_songs(user_id: int):
    sql = """
        SELECT id, track_name, artist_name, track_url, created_at
        FROM saved_songs
        WHERE user_id = %s
        ORDER BY created_at DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()

def remove_song(user_id: int, track_url: str):
    sql = """
        DELETE FROM saved_songs
        WHERE user_id = %s AND track_url = %s
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, (user_id, track_url))
