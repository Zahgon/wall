"""Shared test fixtures.

Storage roots are redirected into a throwaway directory before the application
package is imported, so running the suite never writes into the project tree.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterator

import pytest

_SCRATCH = Path(tempfile.mkdtemp(prefix="wall-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_SCRATCH / 'db.sqlite3'}"
os.environ["MEDIA_ROOT"] = str(_SCRATCH / "media")
os.environ["STATIC_ROOT"] = str(_SCRATCH / "static")

from fastapi import APIRouter, FastAPI  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import accounts.models  # noqa: E402,F401  (registers the mapping)
import ads.models  # noqa: E402,F401  (registers the mapping)
from accounts.managers import UserManager  # noqa: E402
from accounts.models import User  # noqa: E402
from ads.models import Ad  # noqa: E402
from wall.database import Base, SessionLocal, engine, get_session  # noqa: E402
from wall.main import app as application  # noqa: E402
from wall.security import create_access_token  # noqa: E402

USERNAME = "amir"
PASSWORD = "test1234"


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Remove the scratch directory once the whole run is over."""
    shutil.rmtree(_SCRATCH, ignore_errors=True)


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """A session against a schema rebuilt from scratch for every test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def app(db_session: Session) -> Iterator[FastAPI]:
    """The application, wired to the test's own session."""
    application.dependency_overrides[get_session] = lambda: db_session
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """An HTTP client speaking to the application in-process."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def user(db_session: Session) -> User:
    """The account the authenticated cases act as."""
    return UserManager(db_session).create_user(username=USERNAME, password=PASSWORD)


@pytest.fixture()
def token(user: User) -> str:
    """A bearer token for :func:`user`."""
    return create_access_token(user.id)


@pytest.fixture()
def auth(token: str) -> dict[str, str]:
    """Headers carrying the bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def ad(db_session: Session) -> Ad:
    """An ad with no publisher and no image, as the original fixtures made it."""
    instance = Ad(title="Iphone", caption="Nice")
    db_session.add(instance)
    db_session.commit()
    db_session.refresh(instance)
    return instance


@pytest.fixture()
def route_named() -> Callable[[APIRouter, str], APIRoute]:
    """Look a route up on its router by the name the path is registered under."""

    def find(router: APIRouter, name: str) -> APIRoute:
        for route in router.routes:
            if isinstance(route, APIRoute) and route.name == name:
                return route
        raise AssertionError(f"no route named {name!r}")

    return find
