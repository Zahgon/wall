"""Database engine, session factory and declarative base."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Column, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from wall.config import settings

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, future=True, connect_args=_connect_args)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
)


class Base(DeclarativeBase):
    """Declarative base exposing the field metadata the models attach to columns."""

    @classmethod
    def get_field(cls, name: str) -> Column:
        """Return the mapped column called ``name``.

        Models annotate their columns with human readable labels through
        ``info={"verbose_name": ...}``; this accessor is how that metadata is
        reached.
        """
        return cls.__table__.columns[name]

    @classmethod
    def verbose_name_of(cls, name: str) -> str:
        return cls.get_field(name).info["verbose_name"]


def load_models() -> None:
    """Import every model module so the mapper registry is complete.

    The two models reference each other by name, so neither can be configured
    until both modules have been imported.
    """
    from accounts import models as _accounts  # noqa: F401
    from ads import models as _ads  # noqa: F401


def create_all() -> None:
    """Create every mapped table that does not exist yet."""
    load_models()
    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
