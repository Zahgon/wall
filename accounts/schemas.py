"""Request and response bodies for the accounts endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

USERNAME_MAX_LENGTH = 40


class UserSchema(BaseModel):
    """What a user looks like on the way out."""

    model_config = ConfigDict(from_attributes=True)

    username: str


class UserUpdate(BaseModel):
    """What a user update accepts on the way in."""

    username: str = Field(max_length=USERNAME_MAX_LENGTH)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    refresh: str
    access: str
