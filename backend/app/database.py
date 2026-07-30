import json
import os
import secrets
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.errors


IntegrityError = psycopg2.errors.UniqueViolation


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. DevProof now requires a Postgres database "
            "(SQLite is no longer used) - see backend/.env.example."
        )
    return url


@contextmanager
def get_connection():
    connection = psycopg2.connect(_database_url(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS repositories (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    user_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT (now())::text,
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
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    github_id BIGINT NOT NULL UNIQUE,
                    github_username TEXT NOT NULL,
                    avatar_url TEXT,
                    access_token TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (now())::text
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (now())::text
                )
                """
            )


def insert_repository(url: str, user_id: int) -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO repositories (url, user_id) VALUES (%s, %s) RETURNING id",
                (url, user_id),
            )
            return cursor.fetchone()["id"]


def get_all_repositories(user_id: int) -> list[dict]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM repositories WHERE user_id = %s",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]


def get_repository_by_id(repository_id: int, user_id: int) -> dict | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM repositories WHERE id = %s AND user_id = %s",
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
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE repositories
                SET stars = %s,
                    forks = %s,
                    language = %s,
                    description = %s,
                    owner = %s,
                    recent_commit_count = %s,
                    last_fetched_at = (now())::text
                WHERE id = %s AND user_id = %s
                """,
                (stars, forks, language, description, owner, recent_commit_count, repository_id, user_id),
            )


def update_repository_analysis(repository_id: int, user_id: int, report: dict) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE repositories
                SET analysis_report = %s,
                    analyzed_at = (now())::text
                WHERE id = %s AND user_id = %s
                """,
                (json.dumps(report), repository_id, user_id),
            )


def delete_repository(repository_id: int, user_id: int) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM repositories WHERE id = %s AND user_id = %s",
                (repository_id, user_id),
            )
            return cursor.rowcount > 0


def get_or_create_user(github_id: int, github_username: str, avatar_url: str | None, access_token: str) -> dict:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (github_id, github_username, avatar_url, access_token)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (github_id) DO UPDATE SET
                    github_username = EXCLUDED.github_username,
                    avatar_url = EXCLUDED.avatar_url,
                    access_token = EXCLUDED.access_token
                """,
                (github_id, github_username, avatar_url, access_token),
            )
            cursor.execute(
                "SELECT * FROM users WHERE github_id = %s",
                (github_id,),
            )
            return dict(cursor.fetchone())


def create_session(user_id: int) -> str:
    session_id = secrets.token_urlsafe(32)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)",
                (session_id, user_id),
            )
    return session_id


def get_user_by_session(session_id: str) -> dict | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT users.*
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.session_id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row is not None else None


def delete_session(session_id: str) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM sessions WHERE session_id = %s",
                (session_id,),
            )
