import json
import secrets
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
                url TEXT NOT NULL,
                user_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                stars INTEGER,
                forks INTEGER,
                language TEXT,
                description TEXT,
                owner TEXT,
                recent_commit_count INTEGER,
                last_fetched_at TEXT,
                analysis_report TEXT,
                analyzed_at TEXT,
                UNIQUE (url, user_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id INTEGER NOT NULL UNIQUE,
                github_username TEXT NOT NULL,
                avatar_url TEXT,
                access_token TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def insert_repository(url: str, user_id: int) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO repositories (url, user_id) VALUES (?, ?)",
            (url, user_id),
        )
        return cursor.lastrowid


def get_all_repositories(user_id: int) -> list[dict]:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "SELECT * FROM repositories WHERE user_id = ?",
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_repository_by_id(repository_id: int, user_id: int) -> dict | None:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "SELECT * FROM repositories WHERE id = ? AND user_id = ?",
            (repository_id, user_id),
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None


def update_repository_github_data(
    repository_id: int,
    user_id: int,
    stars: int,
    forks: int,
    language: str | None,
    description: str | None,
    owner: str,
    recent_commit_count: int,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE repositories
            SET stars = ?,
                forks = ?,
                language = ?,
                description = ?,
                owner = ?,
                recent_commit_count = ?,
                last_fetched_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (stars, forks, language, description, owner, recent_commit_count, repository_id, user_id),
        )


def update_repository_analysis(repository_id: int, user_id: int, report: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE repositories
            SET analysis_report = ?,
                analyzed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (json.dumps(report), repository_id, user_id),
        )


def delete_repository(repository_id: int, user_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM repositories WHERE id = ? AND user_id = ?",
            (repository_id, user_id),
        )
        return cursor.rowcount > 0


def get_or_create_user(github_id: int, github_username: str, avatar_url: str | None, access_token: str) -> dict:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        connection.execute(
            """
            INSERT INTO users (github_id, github_username, avatar_url, access_token)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (github_id) DO UPDATE SET
                github_username = excluded.github_username,
                avatar_url = excluded.avatar_url,
                access_token = excluded.access_token
            """,
            (github_id, github_username, avatar_url, access_token),
        )
        cursor = connection.execute(
            "SELECT * FROM users WHERE github_id = ?",
            (github_id,),
        )
        return dict(cursor.fetchone())


def create_session(user_id: int) -> str:
    session_id = secrets.token_urlsafe(32)
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
            (session_id, user_id),
        )
    return session_id


def get_user_by_session(session_id: str) -> dict | None:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.session_id = ?
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None


def delete_session(session_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            (session_id,),
        )