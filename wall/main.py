"""Application entrypoint: wiring, docs and static media."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import yaml
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse, Response
from starlette.staticfiles import StaticFiles

from accounts.routes import router as accounts_router
from ads.routes import router as ads_router
from wall.config import settings
from wall.database import create_all
from wall.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Make sure the storage roots and the schema exist before serving."""
    settings.media_root.mkdir(parents=True, exist_ok=True)
    settings.static_root.mkdir(parents=True, exist_ok=True)
    create_all()
    yield


def create_app() -> FastAPI:
    """Build the ASGI application with the documented surface only."""
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )

    # Paths are matched exactly: a trailing slash was never an alias for the
    # canonical path, it simply did not resolve.
    app.router.redirect_slashes = False

    register_exception_handlers(app)

    app.include_router(accounts_router, prefix="/api/accounts")
    app.include_router(ads_router, prefix="/api/ads")

    app.mount(
        settings.media_url.rstrip("/"),
        StaticFiles(directory=settings.media_root, check_dir=False),
        name="media",
    )
    app.mount(
        settings.static_url.rstrip("/"),
        StaticFiles(directory=settings.static_root, check_dir=False),
        name="static",
    )

    @app.get("/schema/", name="schema", include_in_schema=False)
    async def schema() -> Response:
        """Serve the OpenAPI document as YAML, as the original schema view did."""
        document = yaml.safe_dump(app.openapi(), allow_unicode=True, sort_keys=False)
        return Response(content=document, media_type="application/vnd.oai.openapi")

    @app.get("/swagger/", name="swagger-ui", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        """Serve the interactive documentation pointed at the schema view."""
        return get_swagger_ui_html(openapi_url="/schema/", title=settings.api_title)

    return app


app = create_app()
