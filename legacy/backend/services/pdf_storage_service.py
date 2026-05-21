import re
import shutil
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "pdf_files.db"
GENERATED_PDF_DIR = PROJECT_ROOT / "generated_pdfs"
LATEST_PDF_PATH = PROJECT_ROOT / "research_paper.pdf"


def init_db() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pdf_files (
                id INTEGER PRIMARY KEY,
                topic TEXT,
                filename TEXT,
                filepath TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _filename_for_topic(topic: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip().lower()).strip("_")
    return f"{slug or 'research_paper'}.pdf"


def _unique_filename(filename: str) -> str:
    target = GENERATED_PDF_DIR / filename
    if not target.exists():
        return filename

    stem = target.stem
    suffix = target.suffix
    counter = 2

    while True:
        candidate = f"{stem}_{counter}{suffix}"
        if not (GENERATED_PDF_DIR / candidate).exists():
            return candidate
        counter += 1


def store_generated_pdf(topic: str) -> dict | None:
    init_db()

    if not LATEST_PDF_PATH.exists():
        return None

    GENERATED_PDF_DIR.mkdir(exist_ok=True)
    filename = _unique_filename(_filename_for_topic(topic))
    destination = GENERATED_PDF_DIR / filename
    shutil.copy2(LATEST_PDF_PATH, destination)

    relative_path = destination.relative_to(PROJECT_ROOT).as_posix()

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO pdf_files (topic, filename, filepath)
            VALUES (?, ?, ?)
            """,
            (topic, filename, relative_path),
        )
        row_id = cursor.lastrowid

    return {
        "id": row_id,
        "topic": topic,
        "filename": filename,
        "filepath": relative_path,
    }


def get_latest_pdf() -> dict | None:
    init_db()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, topic, filename, filepath, created_at
            FROM pdf_files
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    return dict(row) if row else None


def list_pdf_files() -> list[dict]:
    init_db()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, topic, filename, filepath, created_at
            FROM pdf_files
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]
