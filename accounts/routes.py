"""Accounts endpoints: obtaining a token pair and reading or editing a profile."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from accounts.managers import UserManager
from accounts.models import User
from accounts.schemas import LoginRequest, TokenPair, UserSchema, UserUpdate
from wall.dependencies import CurrentUser, DatabaseSession
from wall.exceptions import INVALID_CREDENTIALS, NotAuthenticated, ValidationError
from wall.i18n import _
from wall.parsers import parse_data
from wall.security import create_access_token, create_refresh_token
from wall.validation import validate

router = APIRouter()

USERNAME_TAKEN = "user with this username already exists."


@router.post("/login", name="login", response_model=TokenPair)
async def login(request: Request, session: DatabaseSession) -> TokenPair:
    """Exchange a username and password for a refresh/access token pair."""
    credentials = validate(LoginRequest, await parse_data(request))
    user = UserManager(session).get_by_natural_key(credentials.username)
    if user is None or not user.is_active or not user.check_password(credentials.password):
        raise NotAuthenticated(INVALID_CREDENTIALS)
    return TokenPair(
        refresh=create_refresh_token(user.id), access=create_access_token(user.id)
    )


@router.api_route(
    "/profile", methods=["GET", "PUT"], name="profile_view", response_model=UserSchema
)
async def profile_view(
    request: Request, user: CurrentUser, session: DatabaseSession
) -> UserSchema:
    """Return the authenticated user, or replace it with the submitted body."""
    if request.method == "PUT":
        payload = validate(UserUpdate, await parse_data(request))
        taken = session.scalar(
            select(User).where(User.username == payload.username, User.id != user.id)
        )
        if taken is not None:
            raise ValidationError({"username": [_(USERNAME_TAKEN)]})
        user.username = payload.username
        session.commit()
        session.refresh(user)
    return UserSchema.model_validate(user)
