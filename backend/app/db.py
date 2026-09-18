"""SQLite persistence for the Thompson Sampling recommendation engine.

Kept deliberately simple (stdlib sqlite3, no ORM) since the bandit state is
just a handful of small tables: posterior parameters per (context, content)
arm, and a log of served recommendations used to match feedback back to the
arm that produced them.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("BANDIT_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "bandit.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS bandit_arms (
    context_key TEXT NOT NULL,
    content_id  TEXT NOT NULL,
    alpha       REAL NOT NULL DEFAULT 1.0,
    beta        REAL NOT NULL DEFAULT 1.0,
    pulls       INTEGER NOT NULL DEFAULT 0,
    rewards     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (context_key, content_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    rec_id      TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    context_key TEXT NOT NULL,
    content_id  TEXT NOT NULL,
    served_at   TEXT NOT NULL,
    rewarded    INTEGER,
    rewarded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);
"""


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def session(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_or_create_arm(conn: sqlite3.Connection, context_key: str, content_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM bandit_arms WHERE context_key = ? AND content_id = ?",
        (context_key, content_id),
    ).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO bandit_arms (context_key, content_id) VALUES (?, ?)",
            (context_key, content_id),
        )
        row = conn.execute(
            "SELECT * FROM bandit_arms WHERE context_key = ? AND content_id = ?",
            (context_key, content_id),
        ).fetchone()
    return row


def update_arm(conn: sqlite3.Connection, context_key: str, content_id: str, reward: int) -> None:
    conn.execute(
        """
        UPDATE bandit_arms
        SET alpha = alpha + ?,
            beta = beta + ?,
            pulls = pulls + 1,
            rewards = rewards + ?
        WHERE context_key = ? AND content_id = ?
        """,
        (reward, 1 - reward, reward, context_key, content_id),
    )


def log_recommendation(conn: sqlite3.Connection, user_id: str, context_key: str, content_id: str) -> str:
    rec_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO recommendations (rec_id, user_id, context_key, content_id, served_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (rec_id, user_id, context_key, content_id, datetime.now(timezone.utc).isoformat()),
    )
    return rec_id


def get_recommendation(conn: sqlite3.Connection, rec_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM recommendations WHERE rec_id = ?", (rec_id,)
    ).fetchone()


def mark_recommendation_rewarded(conn: sqlite3.Connection, rec_id: str, reward: int) -> None:
    conn.execute(
        "UPDATE recommendations SET rewarded = ?, rewarded_at = ? WHERE rec_id = ?",
        (reward, datetime.now(timezone.utc).isoformat(), rec_id),
    )


def arms_for_context(conn: sqlite3.Connection, context_key: str):
    return conn.execute(
        "SELECT * FROM bandit_arms WHERE context_key = ? ORDER BY content_id", (context_key,)
    ).fetchall()
