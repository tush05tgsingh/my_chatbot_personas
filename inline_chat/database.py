import sqlite3
import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path

def init_db(db_path: Path) -> sqlite3.Connection:
    """Create tables if they don't exist and return a connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe concurrent writes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            persona_key TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            role        TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    return conn
 
 
def create_session(conn: sqlite3.Connection, persona_key: str) -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())[:8]   # short, readable ID
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO sessions (id, persona_key, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, persona_key, now, now),
    )
    conn.commit()
    return session_id
 
 
def load_session(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    """Return session row or None if not found."""
    return conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
 
 
def save_message(conn: sqlite3.Connection, session_id: str, role: str, content: str):
    """Persist a single message and update session timestamp."""
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, now),
    )
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
 
 
def load_history(conn: sqlite3.Connection, session_id: str, limit: int) -> list[dict]:
    """Return the last `limit` messages as Anthropic-format dicts."""
    rows = conn.execute(
        """
        SELECT role, content FROM messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()
    # rows come back newest-first; reverse so oldest is first
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
 
 
def list_sessions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sessions ORDER BY updated_at DESC"
    ).fetchall()
 
 
def clear_session(conn: sqlite3.Connection, session_id: str):
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()