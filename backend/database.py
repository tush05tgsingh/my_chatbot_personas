import os
from sqlalchemy import create_engine
import psycopg
from dotenv import load_dotenv
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL","")
print(SQLALCHEMY_DATABASE_URL)

def get_db():
    conn = psycopg.connect(SQLALCHEMY_DATABASE_URL)
    # conn.cursor_factory = psycopg.extras.RealDictCursor  # same as sqlite3.Row — returns dict-like rows
    return conn
 
 
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         TEXT PRIMARY KEY,
            email      TEXT UNIQUE NOT NULL,
            username   TEXT UNIQUE NOT NULL,
            hashed_pw  TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            persona_key TEXT NOT NULL,
            title       TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()

if __name__=="__main__":
    init_db()