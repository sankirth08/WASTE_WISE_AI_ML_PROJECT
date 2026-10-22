import sqlite3
import time


def create_user(connection: sqlite3.Connection, name: str, email: str, password_hash: str) -> int:
	cursor = connection.execute(
		"INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
		(name, email, password_hash, int(time.time())),
	)
	return int(cursor.lastrowid)


def get_user_by_email(connection: sqlite3.Connection, email: str) -> sqlite3.Row | None:
	return connection.execute(
		"SELECT id, name, email, password_hash FROM users WHERE email = ? COLLATE NOCASE",
		(email,),
	).fetchone()
