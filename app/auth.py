import sqlite3
import uuid
from typing import Optional
from app.repository import get_db, DEFAULT_DB_PATH

def init_users_db(db_path: str = DEFAULT_DB_PATH):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                learner_id TEXT NOT NULL
            );
        """)
        conn.commit()

def register_user(username: str, password: str, db_path: str = DEFAULT_DB_PATH) -> Optional[str]:
    init_users_db(db_path)
    learner_id = f"learner-{uuid.uuid4().hex[:8]}"
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, learner_id) VALUES (?, ?, ?)", (username, password, learner_id))
            conn.commit()
            return learner_id
        except sqlite3.IntegrityError:
            return None # Username exists

def authenticate_user(username: str, password: str, db_path: str = DEFAULT_DB_PATH) -> Optional[str]:
    init_users_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT learner_id FROM users WHERE username = ? AND password = ?", (username, password))
        row = cursor.fetchone()
        if row:
            return row["learner_id"]
        return None
