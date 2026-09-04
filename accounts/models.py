"""The user model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wall.database import Base
from wall.i18n import _
from wall.security import check_password, make_password

if TYPE_CHECKING:
    from ads.models import Ad

USERNAME_FIELD = "username"


class User(Base):
    """A person able to authenticate against the API."""

    __tablename__ = "accounts_user"

    verbose_name = _("user")
    verbose_name_plural = _("users")

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    password: Mapped[str] = mapped_column(String(128), default="")
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    username: Mapped[str] = mapped_column(
        String(40), unique=True, info={"verbose_name": _("username")}
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    ad: Mapped[list[Ad]] = relationship(back_populates="publisher")

    def __str__(self) -> str:
        return self.username

    def __repr__(self) -> str:
        return f"<User: {self.username}>"

    def set_password(self, raw_password: str | None) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str | None) -> bool:
        return check_password(raw_password, self.password)

    def has_perm(self, perm: str, obj: object | None = None) -> bool:
        return True

    def has_module_perms(self, app_label: str) -> bool:
        return True

    @property
    def is_staff(self) -> bool:
        return self.is_admin
