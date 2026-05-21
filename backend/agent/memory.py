from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    input_prompt TEXT NOT NULL,
                    output_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    plan_json TEXT,
                    drive_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    title TEXT,
                    url TEXT,
                    snippet TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    extracted_preview TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                """
            )

    def save_run(
        self,
        topic: str,
        input_prompt: str,
        output_type: str,
        content: str,
        plan: dict[str, Any],
        sources: list[dict[str, Any]],
        drive_link: str | None = None,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO runs (topic, input_prompt, output_type, content, plan_json, drive_link)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    topic,
                    input_prompt,
                    output_type,
                    content,
                    json.dumps(plan),
                    drive_link,
                ),
            )
            run_id = int(cursor.lastrowid)
            for source in sources:
                conn.execute(
                    """
                    INSERT INTO sources (run_id, title, url, snippet)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        source.get("title"),
                        source.get("url"),
                        source.get("snippet"),
                    ),
                )
        return {"run_id": run_id, "output_id": run_id, "source_count": len(sources)}

    def update_drive_link(self, output_id: int, drive_link: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET drive_link = ? WHERE id = ?",
                (drive_link, output_id),
            )

    def save_uploaded_file(
        self,
        filename: str,
        file_type: str,
        file_path: str,
        extracted_preview: str,
        run_id: int | None = None,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO uploaded_files (run_id, filename, file_type, file_path, extracted_preview)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, filename, file_type, file_path, extracted_preview),
            )
            file_id = int(cursor.lastrowid)
        return {"id": file_id, "filename": filename, "file_path": file_path}

    def save_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        run_id: int | None = None,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (run_id, event_type, payload_json)
                VALUES (?, ?, ?)
                """,
                (run_id, event_type, json.dumps(payload)),
            )
            event_id = int(cursor.lastrowid)
        return {"status": "success", "event_id": event_id}

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, topic, input_prompt, output_type, content, drive_link, created_at
                FROM runs
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

            items: list[dict[str, Any]] = []
            for row in rows:
                source_rows = conn.execute(
                    """
                    SELECT title, url, snippet
                    FROM sources
                    WHERE run_id = ?
                    ORDER BY id ASC
                    """,
                    (row["id"],),
                ).fetchall()
                file_rows = conn.execute(
                    """
                    SELECT id, filename, file_type, file_path, created_at
                    FROM uploaded_files
                    WHERE run_id = ?
                    ORDER BY id ASC
                    """,
                    (row["id"],),
                ).fetchall()
                items.append(
                    {
                        "output_id": row["id"],
                        "topic": row["topic"],
                        "input_prompt": row["input_prompt"],
                        "output_type": row["output_type"],
                        "content": row["content"],
                        "content_preview": row["content"][:800],
                        "drive_link": row["drive_link"],
                        "created_at": row["created_at"],
                        "sources": [dict(source_row) for source_row in source_rows],
                        "files": [dict(file_row) for file_row in file_rows],
                    }
                )
        return items