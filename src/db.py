import os
import sqlite3

from src.utils import DEFAULT_DB_FILE_PATH, get_configs


def get_db_conn():
    configs = get_configs()

    conn = sqlite3.connect(configs["db_path"])
    conn.row_factory = sqlite3.Row

    return conn


def create_db(db_path: str | None = None):
    if not db_path:
        db_path = os.environ.get("DB_PATH", DEFAULT_DB_FILE_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS spotify_tokens (
            id INTEGER PRIMARY KEY,
            token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            expires_in DATETIME NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()
