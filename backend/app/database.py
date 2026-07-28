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