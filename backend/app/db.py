"""Database connection and initialization using Turso (libsql)."""

import libsql_experimental as libsql

from app.config import settings

_conn = None


async def get_db():
    global _conn
    if _conn is None:
        url = settings.TURSO_DATABASE_URL
        auth_token = settings.TURSO_AUTH_TOKEN
        if url and auth_token:
            _conn = libsql.connect(database=url, auth_token=auth_token)
        else:
            _conn = libsql.connect("helix.db")
    return _conn


async def init_db():
    conn = await get_db()
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            url TEXT,
            status TEXT,
            final_status TEXT,
            started_at TEXT,
            completed_at TEXT,
            error TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS iterations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT REFERENCES runs(id),
            step INTEGER,
            url TEXT,
            answer TEXT,
            correct BOOLEAN,
            next_url TEXT,
            explanation TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
