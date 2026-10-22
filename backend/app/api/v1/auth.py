import sqlite3
import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import (
	create_access_token,
	hash_access_token,
	hash_password,
	verify_password,
)
from app.dependencies import get_current_user, get_db
from app.models.user import create_user, get_user_by_email
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_TTL_SECONDS = 60 * 60 * 24


def create_session(connection: sqlite3.Connection, user_id: int) -> str:
	token = create_access_token()
	connection.execute(
		"INSERT INTO auth_sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
		(hash_access_token(token), user_id, int(time.time()) + SESSION_TTL_SECONDS),
	)
	return token


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, connection: sqlite3.Connection = Depends(get_db)) -> AuthResponse:
	if get_user_by_email(connection, payload.email) is not None:
		raise HTTPException(status_code=409, detail="An account with this email already exists")
	try:
		user_id = create_user(connection, payload.name, payload.email, hash_password(payload.password))
		token = create_session(connection, user_id)
		connection.commit()
	except sqlite3.IntegrityError as error:
		connection.rollback()
		raise HTTPException(status_code=409, detail="An account with this email already exists") from error
	return AuthResponse(
		access_token=token,
		user=UserResponse(id=user_id, name=payload.name, email=payload.email),
	)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, connection: sqlite3.Connection = Depends(get_db)) -> AuthResponse:
	user = get_user_by_email(connection, payload.email)
	if user is None or not verify_password(payload.password, user["password_hash"]):
		raise HTTPException(status_code=401, detail="Email or password is incorrect")
	token = create_session(connection, int(user["id"]))
	connection.commit()
	return AuthResponse(
		access_token=token,
		user=UserResponse(id=int(user["id"]), name=user["name"], email=user["email"]),
	)


@router.get("/me", response_model=UserResponse)
def current_user(user: dict[str, object] = Depends(get_current_user)) -> UserResponse:
	return UserResponse(**user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
	user: dict[str, object] = Depends(get_current_user),
	connection: sqlite3.Connection = Depends(get_db),
) -> None:
	connection.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user["id"],))
	connection.commit()
