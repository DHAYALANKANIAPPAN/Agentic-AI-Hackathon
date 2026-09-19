"""SQLite Repository for EduPath (Member B).

Manages persistence for learners, activity_log, and struggle_flags.
"""

import contextlib
import json
import sqlite3
from datetime import datetime
from typing import Optional, List
from shared.schemas.models import (
    LearnerState,
    SkillProfile,
    GapList,
    WeeklyPlan,
    ActivityLog,
    StruggleFlag,
)

DEFAULT_DB_PATH = "edupath.db"


@contextlib.contextmanager
def get_db(db_path: str = DEFAULT_DB_PATH):
    """Context manager that ensures SQLite connections are properly closed."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create and return a SQLite connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize SQLite database tables: learners, activity_log, and struggle_flags."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learners (
                id TEXT PRIMARY KEY,
                target_role TEXT NOT NULL,
                profile_json TEXT NOT NULL,
                gaps_json TEXT NOT NULL,
                plan_json TEXT,
                hours_per_week REAL DEFAULT 10.0,
                weeks_available INTEGER DEFAULT 4,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                minutes_spent INTEGER NOT NULL,
                rating TEXT NOT NULL,
                quiz_score REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (learner_id) REFERENCES learners(id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS struggle_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                reason TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (learner_id) REFERENCES learners(id)
            );
        """)
        conn.commit()


def save_learner(learner: LearnerState, db_path: str = DEFAULT_DB_PATH) -> None:
    """Save or update a learner in the database."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        profile_json = learner.profile.model_dump_json() if learner.profile else "{}"
        gaps_json = learner.gaps.model_dump_json() if learner.gaps else "{}"
        plan_json = learner.plan.model_dump_json() if learner.plan else None

        cursor.execute("""
            INSERT OR REPLACE INTO learners (
                id, target_role, profile_json, gaps_json, plan_json, hours_per_week, weeks_available, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            learner.id,
            learner.gaps.target_role if learner.gaps else "General",
            profile_json,
            gaps_json,
            plan_json,
            learner.hours_per_week,
            learner.weeks_available,
            datetime.utcnow().isoformat(),
        ))
        conn.commit()


def get_learner(learner_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[LearnerState]:
    """Retrieve full LearnerState from the database."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learners WHERE id = ?;", (learner_id,))
        row = cursor.fetchone()
        if not row:
            return None

        profile_data = json.loads(row["profile_json"]) if row["profile_json"] else None
        gaps_data = json.loads(row["gaps_json"]) if row["gaps_json"] else None
        plan_data = json.loads(row["plan_json"]) if row["plan_json"] else None

        profile = SkillProfile.model_validate(profile_data) if profile_data else None
        gaps = GapList.model_validate(gaps_data) if gaps_data else None
        plan = WeeklyPlan.model_validate(plan_data) if plan_data else None

        # Fetch activity log
        cursor.execute("SELECT * FROM activity_log WHERE learner_id = ? ORDER BY id ASC;", (learner_id,))
        act_rows = cursor.fetchall()
        activity_logs = [
            ActivityLog(
                item_id=ar["item_id"],
                minutes_spent=ar["minutes_spent"],
                rating=ar["rating"],
                quiz_score=ar["quiz_score"],
                timestamp=datetime.fromisoformat(ar["timestamp"]),
            )
            for ar in act_rows
        ]

        # Fetch struggle flags
        cursor.execute("SELECT * FROM struggle_flags WHERE learner_id = ? ORDER BY id ASC;", (learner_id,))
        flag_rows = cursor.fetchall()
        struggle_flags = [
            StruggleFlag(
                skill_name=fr["skill_name"],
                reason=fr["reason"],
                severity=fr["severity"],
            )
            for fr in flag_rows
        ]

        return LearnerState(
            id=row["id"],
            profile=profile,
            gaps=gaps,
            plan=plan,
            activity_log=activity_logs,
            struggle_flags=struggle_flags,
            hours_per_week=row["hours_per_week"],
            weeks_available=row["weeks_available"],
        )


def log_activity(learner_id: str, activity: ActivityLog, db_path: str = DEFAULT_DB_PATH) -> None:
    """Insert an entry into activity_log."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (learner_id, item_id, minutes_spent, rating, quiz_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (
            learner_id,
            activity.item_id,
            activity.minutes_spent,
            activity.rating.value if hasattr(activity.rating, "value") else str(activity.rating),
            activity.quiz_score,
            activity.timestamp.isoformat(),
        ))
        conn.commit()


def save_struggle_flag(learner_id: str, flag: StruggleFlag, db_path: str = DEFAULT_DB_PATH) -> None:
    """Insert an entry into struggle_flags."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO struggle_flags (learner_id, skill_name, reason, severity, timestamp)
            VALUES (?, ?, ?, ?, ?);
        """, (
            learner_id,
            flag.skill_name,
            flag.reason,
            flag.severity,
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
