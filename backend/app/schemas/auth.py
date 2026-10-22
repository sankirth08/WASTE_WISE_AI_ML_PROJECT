import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
	name: str = Field(min_length=1, max_length=100)
	email: str = Field(min_length=3, max_length=254)
	password: str = Field(min_length=8, max_length=128)

	@field_validator("name")
	@classmethod
	def normalize_name(cls, value: str) -> str:
		name = value.strip()
		if not name:
			raise ValueError("Name is required")
		return name

	@field_validator("email")
	@classmethod
	def normalize_email(cls, value: str) -> str:
		email = value.strip().lower()
		if not EMAIL_PATTERN.fullmatch(email):
			raise ValueError("Enter a valid email address")
		return email


class LoginRequest(BaseModel):
	email: str = Field(min_length=3, max_length=254)
	password: str = Field(min_length=1, max_length=128)

	@field_validator("email")
	@classmethod
	def normalize_email(cls, value: str) -> str:
		email = value.strip().lower()
		if not EMAIL_PATTERN.fullmatch(email):
			raise ValueError("Enter a valid email address")
		return email


class UserResponse(BaseModel):
	id: int
	name: str
	email: str


class AuthResponse(BaseModel):
	access_token: str
	token_type: str = "bearer"
	user: UserResponse