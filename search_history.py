import time
import streamlit as st

def _key(user_id: int | str) -> str:
    return f"search_history_{user_id}"

def record_search(user_id, query_type: str, query_text: str) -> None:
    if not user_id or not query_text:
        return

    k = _key(user_id)
    history = st.session_state.get(k, [])

    entry = {
        "id": int(time.time() * 1000),   # unique-ish id
        "query_type": query_type,
        "query_text": query_text,
        "ts": time.time(),
    }

    # prevent duplicates back-to-back
    if history and history[0]["query_type"] == query_type and history[0]["query_text"] == query_text:
        return

    history.insert(0, entry)
    st.session_state[k] = history[:10]  

def get_recent_searches(user_id, limit: int = 5):
    k = _key(user_id)
    history = st.session_state.get(k, [])
    return history[:limit]