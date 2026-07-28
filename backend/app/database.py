import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parents[1] / "devproof.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def insert_repository(url: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO repositories (url) VALUES (?)",
            (url,),
        )
        return cursor.lastrowid


def get_all_repositories() -> list[dict]:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("SELECT id, url, created_at FROM repositories")
        return [dict(row) for row in cursor.fetchall()]


def get_repository_by_id(repository_id: int) -> dict | None:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "SELECT id, url, created_at FROM repositories WHERE id = ?",
            (repository_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None