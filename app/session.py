"""
Minimal in-memory session store, keyed by user_id.

This is fine for local testing and single-instance demos. It is NOT durable —
a Cloud Run restart or scale-to-zero event wipes it. For production, swap this
for Firestore or Redis (Memorystore) without touching agent.py or main.py:
just change get_history()/save_history() to read/write there instead.
"""
from app.agent import SYSTEM_PROMPT

_SESSIONS: dict = {}


def get_history(user_id: str) -> list:
    if user_id not in _SESSIONS:
        _SESSIONS[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return _SESSIONS[user_id]


def reset_history(user_id: str) -> None:
    _SESSIONS.pop(user_id, None)
