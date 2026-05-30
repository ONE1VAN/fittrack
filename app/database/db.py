import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "fittrack.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_conn: sqlite3.Connection | None = None

def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON;")
        has_schema = _conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not has_schema:
            init_db(_conn)
        _run_migrations(_conn)
    return _conn


def _run_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS subscription_requests (
            req_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id      INTEGER NOT NULL,
            type_id        INTEGER NOT NULL,
            status         TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','approved','rejected')),
            requested_at   TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_at    TEXT,
            FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (type_id)   REFERENCES subscription_types(type_id) ON DELETE RESTRICT
        );
        CREATE INDEX IF NOT EXISTS idx_subreq_status ON subscription_requests(status);
        """
    )
    conn.commit()

def init_db(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    from .seed import seed_demo_data
    seed_demo_data(conn)
    conn.commit()

def reset_db() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    if DB_PATH.exists():
        os.remove(DB_PATH)
    get_db()
