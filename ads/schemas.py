"""Pydantic schemas for the ads app."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from wall.config import settings

TITLE_MAX_LENGTH = 150


class AdSchema(BaseModel):
    """Public representation of an ad.

    The publisher is deliberately absent: the original serializer declared it as
    a read-only field sourced from an attribute the model does not expose, so it
    was skipped for every instance and never reached the payload.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    date_added: datetime
    title: str
    caption: str
    image: str | None
    is_public: bool

    @field_serializer("date_added")
    def _serialize_date_added(self, value: datetime) -> str:
        moment = value if value.tzinfo else value.replace(tzinfo=UTC)
        return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @classmethod
    def from_ad(cls, ad: object) -> AdSchema:
        """Build a payload, expanding the stored image name into a URL."""
        name = getattr(ad, "image", "") or ""
        return cls(
            id=ad.id,
            date_added=ad.date_added,
            title=ad.title,
            caption=ad.caption,
            image=f"{settings.media_url}{name}" if name else None,
            is_public=ad.is_public,
        )


class AdWrite(BaseModel):
    """Writable fields of an ad; id, date_added and is_public are read-only."""

    title: str = Field(max_length=TITLE_MAX_LENGTH)
    caption: str


class PaginatedAds(BaseModel):
    """The paginated envelope returned by the ad list endpoint."""

    count: int
    next: str | None
    previous: str | None
    results: list[AdSchema]
