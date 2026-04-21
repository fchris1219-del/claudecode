import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from mobile_server.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    notes       TEXT,
    due_date    TEXT,
    priority    INTEGER DEFAULT 0,
    list        TEXT DEFAULT 'Inbox',
    completed   INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS routines (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    enabled     INTEGER DEFAULT 1,
    cron        TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS keywords (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,
    keywords    TEXT NOT NULL,
    used        INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    search_date TEXT NOT NULL,
    keywords    TEXT NOT NULL,
    title       TEXT NOT NULL,
    abstract    TEXT,
    authors     TEXT,
    year        INTEGER,
    url         TEXT,
    pdf_url     TEXT,
    created_at  TEXT NOT NULL
);
"""


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def get_db():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
