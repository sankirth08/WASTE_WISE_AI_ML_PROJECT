import base64
import hashlib
import secrets


PASSWORD_ITERATIONS = 310_000


def hash_password(password: str) -> str:
	salt = secrets.token_bytes(16)
	digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
	return "pbkdf2_sha256${}${}${}".format(
		PASSWORD_ITERATIONS,
		base64.urlsafe_b64encode(salt).decode("ascii"),
		base64.urlsafe_b64encode(digest).decode("ascii"),
	)


def verify_password(password: str, encoded_hash: str) -> bool:
	try:
		algorithm, iterations, encoded_salt, encoded_digest = encoded_hash.split("$", 3)
		if algorithm != "pbkdf2_sha256":
			return False
		salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
		expected = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
		actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
		return secrets.compare_digest(actual, expected)
	except (ValueError, TypeError):
		return False


def create_access_token() -> str:
	return secrets.token_urlsafe(32)


def hash_access_token(token: str) -> str:
	return hashlib.sha256(token.encode("utf-8")).hexdigest()
