"""Password hashing and JSON Web Token helpers.

The password encoding is the salted PBKDF2-SHA256 format the project already
stored in its database, so existing rows keep working unchanged. Tokens carry
the same claim set the project issued before.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from wall.config import settings

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 390_000
SALT_ENTROPY = 128
UNUSABLE_PASSWORD_PREFIX = "!"
UNUSABLE_PASSWORD_SUFFIX_LENGTH = 40

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

_ALPHANUMERIC = string.ascii_letters + string.digits


def get_random_string(length: int, allowed_chars: str = _ALPHANUMERIC) -> str:
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def _salt() -> str:
    char_count = int(SALT_ENTROPY // 5.954)  # log_2(len(alphabet)) per character
    return get_random_string(char_count)


def make_password(password: str | None, salt: str | None = None) -> str:
    """Encode ``password``; ``None`` produces an unusable password."""
    if password is None:
        return UNUSABLE_PASSWORD_PREFIX + get_random_string(
            UNUSABLE_PASSWORD_SUFFIX_LENGTH
        )
    salt = salt or _salt()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), ITERATIONS
    )
    encoded = base64.b64encode(digest).decode().strip()
    return f"{ALGORITHM}${ITERATIONS}${salt}${encoded}"


def is_password_usable(encoded: str | None) -> bool:
    return encoded is not None and not encoded.startswith(UNUSABLE_PASSWORD_PREFIX)


def check_password(password: str | None, encoded: str | None) -> bool:
    """Constant-time comparison of ``password`` against a stored hash."""
    if password is None or not is_password_usable(encoded):
        return False
    try:
        algorithm, iterations, salt, _digest = encoded.split("$", 3)
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    candidate = make_password(password, salt)
    candidate_iterations = candidate.split("$", 2)[1]
    if candidate_iterations != iterations:
        candidate = f"{algorithm}${iterations}${salt}${candidate.split('$', 3)[3]}"
    return hmac.compare_digest(candidate, encoded)


def _encode(user_id: int, token_type: str, lifetime: timedelta) -> str:
    issued_at = datetime.now(UTC)
    payload: dict[str, Any] = {
        "token_type": token_type,
        "exp": issued_at + lifetime,
        "iat": issued_at,
        "jti": uuid.uuid4().hex,
        "user_id": user_id,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _encode(user_id, ACCESS_TOKEN_TYPE, settings.access_token_lifetime)


def create_refresh_token(user_id: int) -> str:
    return _encode(user_id, REFRESH_TOKEN_TYPE, settings.refresh_token_lifetime)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify ``token``; raises :class:`jwt.PyJWTError` when invalid."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
