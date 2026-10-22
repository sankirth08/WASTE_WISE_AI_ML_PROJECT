import os
import sqlite3
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(os.getenv("WASTEWISE_DATABASE_PATH", BACKEND_DIR / "data" / "wastewise.db"))


def get_connection() -> sqlite3.Connection:
	DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
	connection = sqlite3.connect(DATABASE_PATH, timeout=10, check_same_thread=False)
	connection.row_factory = sqlite3.Row
	connection.execute("PRAGMA foreign_keys = ON")
	return connection


def initialize_database() -> None:
	with get_connection() as connection:
		connection.executescript(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				email TEXT NOT NULL UNIQUE COLLATE NOCASE,
				password_hash TEXT NOT NULL,
				created_at INTEGER NOT NULL
			);

			CREATE TABLE IF NOT EXISTS auth_sessions (
				token_hash TEXT PRIMARY KEY,
				user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
				expires_at INTEGER NOT NULL
			);

			CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiration
				ON auth_sessions(expires_at);
			"""
		)
