import sqlite3
import time
from collections.abc import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import hash_access_token
from app.db.session import get_connection


bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[sqlite3.Connection, None, None]:
	connection = get_connection()
	try:
		yield connection
	finally:
		connection.close()


def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	connection: sqlite3.Connection = Depends(get_db),
) -> dict[str, object]:
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise HTTPException(status_code=401, detail="Sign in to continue")
	user = connection.execute(
		"""
		SELECT users.id, users.name, users.email
		FROM auth_sessions
		JOIN users ON users.id = auth_sessions.user_id
		WHERE auth_sessions.token_hash = ? AND auth_sessions.expires_at > ?
		""",
		(hash_access_token(credentials.credentials), int(time.time())),
	).fetchone()
	if user is None:
		raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
	return dict(user)
