import sqlite3
import uuid
from typing import Optional, List, Dict
from app.repository import get_db, DEFAULT_DB_PATH

def init_users_db(db_path: str = DEFAULT_DB_PATH):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                username TEXT NOT NULL,
                target_role TEXT NOT NULL,
                learner_id TEXT NOT NULL,
                PRIMARY KEY (username, learner_id)
            );
        """)
        conn.commit()

def register_user(username: str, password: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    init_users_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Username exists

def authenticate_user(username: str, password: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    init_users_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        return cursor.fetchone() is not None

def add_user_role(username: str, target_role: str, learner_id: str, db_path: str = DEFAULT_DB_PATH):
    init_users_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_roles (username, target_role, learner_id) VALUES (?, ?, ?)", (username, target_role, learner_id))
        conn.commit()

def get_user_roles(username: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, str]]:
    init_users_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT target_role, learner_id FROM user_roles WHERE username = ?", (username,))
        return [{"target_role": row["target_role"], "learner_id": row["learner_id"]} for row in cursor.fetchall()]
