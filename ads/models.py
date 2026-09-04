"""The advertisement model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wall.database import Base
from wall.i18n import _

if TYPE_CHECKING:
    from accounts.models import User


def now() -> datetime:
    return datetime.now(UTC)


class Ad(Base):
    """Something a user published on the wall."""

    __tablename__ = "ads_ad"

    verbose_name = _("ad")
    verbose_name_plural = _("ads")
    #: Newest first, matching the order the listing endpoint returns.
    default_ordering = ("-date_added",)
    get_latest_by = "date_added"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        info={"verbose_name": _("date published")},
    )
    title: Mapped[str] = mapped_column(
        String(150), info={"verbose_name": _("title")}
    )
    caption: Mapped[str] = mapped_column(Text, info={"verbose_name": _("caption")})
    image: Mapped[str] = mapped_column(
        String(100), default="", info={"verbose_name": _("image")}
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        info={
            "verbose_name": _("is public"),
            "help_text": _("Public Ads will be displayed in the api views."),
        },
    )
    publisher_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("accounts_user.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        info={"verbose_name": _("publisher")},
    )

    publisher: Mapped[User | None] = relationship(back_populates="ad")

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"<Ad: {self.title}>"
