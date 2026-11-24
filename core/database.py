
import json
import sqlite3

from pathlib import Path
from contextlib import closing
from datetime import datetime, timezone


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "gtm.sqlite3"
)

STATE_KEYS = (
    "product",
    "icp_json",
    "approved_icp",
    "research_context",
    "discovery_result",
    "outreach_records",
    "pipelines",
)


def init_db() -> None:

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with closing(sqlite3.connect(DB_PATH)) as conn:

        with conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace (
                    id INTEGER PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)


def save_workspace(state) -> None:

    data = {
        key: state[key]
        for key in STATE_KEYS
        if key in state
    }

    payload = json.dumps(
        data,
        ensure_ascii=False,
    )

    updated_at = datetime.now(
        timezone.utc
    ).isoformat()

    with closing(sqlite3.connect(DB_PATH)) as conn:

        with conn:

            conn.execute("""
                INSERT INTO workspace (
                    id,
                    payload,
                    updated_at
                )
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
            """, (payload, updated_at))


def load_workspace() -> dict:

    with closing(sqlite3.connect(DB_PATH)) as conn:

        row = conn.execute("""
            SELECT payload
            FROM workspace
            WHERE id = 1
        """).fetchone()

    if row is None:
        return {}

    return json.loads(row[0])
