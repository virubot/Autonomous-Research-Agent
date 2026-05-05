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
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER NOT NULL,
                    title TEXT,
                    url TEXT,
                    snippet TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(topic_id) REFERENCES topics(id)
                );

                CREATE TABLE IF NOT EXISTS outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER NOT NULL,
                    input_prompt TEXT NOT NULL,
                    output_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    plan_json TEXT,
                    drive_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(topic_id) REFERENCES topics(id)
                );

                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    extracted_preview TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            topic_cursor = conn.execute(
                "INSERT INTO topics (topic) VALUES (?)",
                (topic,),
            )
            topic_id = topic_cursor.lastrowid

            for source in sources:
                conn.execute(
                    """
                    INSERT INTO sources (topic_id, title, url, snippet)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        topic_id,
                        source.get("title"),
                        source.get("url"),
                        source.get("snippet"),
                    ),
                )

            output_cursor = conn.execute(
                """
                INSERT INTO outputs (
                    topic_id, input_prompt, output_type, content, plan_json, drive_link
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    topic_id,
                    input_prompt,
                    output_type,
                    content,
                    json.dumps(plan),
                    drive_link,
                ),
            )

        return {
            "topic_id": topic_id,
            "output_id": output_cursor.lastrowid,
            "source_count": len(sources),
        }

    def update_drive_link(self, output_id: int, drive_link: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE outputs SET drive_link = ? WHERE id = ?",
                (drive_link, output_id),
            )

    def save_uploaded_file(
        self,
        filename: str,
        file_type: str,
        file_path: str,
        extracted_preview: str,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO uploaded_files (filename, file_type, file_path, extracted_preview)
                VALUES (?, ?, ?, ?)
                """,
                (filename, file_type, file_path, extracted_preview),
            )
            file_id = cursor.lastrowid
        return {"id": file_id, "filename": filename, "file_path": file_path}

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    o.id AS output_id,
                    t.id AS topic_id,
                    t.topic,
                    o.input_prompt,
                    o.output_type,
                    o.content,
                    o.drive_link,
                    o.created_at
                FROM outputs o
                JOIN topics t ON t.id = o.topic_id
                ORDER BY o.created_at DESC, o.id DESC
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
                    WHERE topic_id = ?
                    ORDER BY id ASC
                    """,
                    (row["topic_id"],),
                ).fetchall()

                items.append(
                    {
                        "output_id": row["output_id"],
                        "topic_id": row["topic_id"],
                        "topic": row["topic"],
                        "input_prompt": row["input_prompt"],
                        "output_type": row["output_type"],
                        "content_preview": row["content"][:800],
                        "drive_link": row["drive_link"],
                        "created_at": row["created_at"],
                        "sources": [dict(source_row) for source_row in source_rows],
                    }
                )
        return items
