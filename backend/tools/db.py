from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def save_to_db(data: dict[str, Any], db_path: Path | str) -> dict[str, Any]:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor = conn.execute(
            """
            INSERT INTO agent_events (event_type, payload_json)
            VALUES (?, ?)
            """,
            (data.get("event_type", "agent_event"), json.dumps(data)),
        )
        row_id = cursor.lastrowid

    return {"status": "success", "event_id": row_id}
