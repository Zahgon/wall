"""User creation and lookup.

Creating a user goes through here rather than through the model directly,
because a username has to be normalised first and the raw password has to be
hashed before it reaches the database.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from accounts.models import User
from wall.i18n import _

MINIMUM_USERNAME_LENGTH = 4


class UserManager:
    """Session bound helper for creating and fetching users."""

    model = User

    def __init__(self, session: Session) -> None:
        self.session = session

    @classmethod
    def normalize_username(cls, username: str | None) -> str:
        username = username or ""
        if len(username) < MINIMUM_USERNAME_LENGTH:
            raise ValueError(_("username must have at least 4 characters"))
        return username.lower()

    def get_by_natural_key(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def create_user(self, username: str | None, password: str | None = None) -> User:
        if not username:
            raise ValueError(_("Users must have a username"))
        user = self.model(username=self.normalize_username(username))
        user.set_password(password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def create_superuser(
        self, username: str | None, password: str | None = None
    ) -> User:
        user = self.create_user(username=username, password=password)
        user.is_admin = True
        self.session.commit()
        self.session.refresh(user)
        return user
