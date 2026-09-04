"""Authentication dependency.

Credentials arrive in an ``Authorization`` header holding a bearer token. Every
rejection along the way keeps the body shape the project answered with before:
a ``detail`` message, optionally accompanied by a machine readable ``code`` and
a ``messages`` list describing which token class was tried.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import jwt
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from wall.database import get_session
from wall.exceptions import (
    BAD_AUTHORIZATION_HEADER,
    INVALID_TOKEN,
    NOT_AUTHENTICATED,
    NotAuthenticated,
)
from wall.security import ACCESS_TOKEN_TYPE, decode_token

if TYPE_CHECKING:
    from accounts.models import User

AUTH_HEADER_TYPE = "Bearer"
AUTH_HEADER = {"WWW-Authenticate": f'{AUTH_HEADER_TYPE} realm="api"'}

_TOKEN_NOT_VALID = {
    "code": "token_not_valid",
    "messages": [
        {
            "token_class": "AccessToken",
            "token_type": ACCESS_TOKEN_TYPE,
            "message": "Token is invalid or expired",
        }
    ],
}


def _raw_token(request: Request) -> str:
    header = request.headers.get("authorization")
    if not header:
        raise NotAuthenticated(NOT_AUTHENTICATED)
    parts = header.split()
    if parts[0] != AUTH_HEADER_TYPE:
        raise NotAuthenticated(NOT_AUTHENTICATED)
    if len(parts) != 2:
        raise NotAuthenticated(
            BAD_AUTHORIZATION_HEADER, {"code": "bad_authorization_header"}
        )
    return parts[1]


def get_current_user(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> "User":
    """Resolve the user the bearer token belongs to."""
    from accounts.models import User

    token = _raw_token(request)
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise NotAuthenticated(INVALID_TOKEN, _TOKEN_NOT_VALID) from None

    if payload.get("token_type") != ACCESS_TOKEN_TYPE:
        raise NotAuthenticated(INVALID_TOKEN, _TOKEN_NOT_VALID)

    user_id = payload.get("user_id")
    if user_id is None:
        raise NotAuthenticated(INVALID_TOKEN, _TOKEN_NOT_VALID)

    user = session.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise NotAuthenticated(INVALID_TOKEN, _TOKEN_NOT_VALID)
    return user


CurrentUser = Annotated["User", Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]
