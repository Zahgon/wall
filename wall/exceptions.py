"""Error responses.

The project answered failures with a small, stable set of body shapes:
``{"detail": ...}`` for anything the client cannot fix field-by-field, and a
mapping of field name to a list of messages for invalid input. These helpers
and handlers keep those shapes intact.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from wall.i18n import _

NOT_AUTHENTICATED = "Authentication credentials were not provided."
INVALID_CREDENTIALS = "No active account found with the given credentials"
BAD_AUTHORIZATION_HEADER = (
    "Authorization header must contain two space-delimited values"
)
INVALID_TOKEN = "Given token not valid for any token type"
NOT_FOUND = "Not found."
INVALID_PAGE = "Invalid page."
REQUIRED_FIELD = "This field is required."


INVALID_IMAGE = (
    "Upload a valid image. The file you uploaded was either not an image or a corrupted image."
)
UNSUPPORTED_MEDIA_TYPE = 'Unsupported media type "{media_type}" in request.'
MAX_LENGTH = "Ensure this field has no more than {max_length} characters."
METHOD_NOT_ALLOWED = 'Method "{method}" not allowed.'


def unsupported_media_type(content_type: str) -> str:
    return _(UNSUPPORTED_MEDIA_TYPE).format(media_type=content_type)


def max_length_error(limit: int) -> str:
    return _(MAX_LENGTH).format(max_length=limit)


def method_not_allowed(method: str) -> str:
    return _(METHOD_NOT_ALLOWED).format(method=method)


class DetailError(HTTPException):
    """A failure rendered as ``{"detail": ...}`` plus any extra top level keys."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        extra: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=_(detail), headers=headers)
        self.extra = extra or {}


class ValidationError(HTTPException):
    """Field level failures rendered as ``{field: [message, ...]}``."""

    def __init__(self, errors: dict[str, list[str]]) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
        self.errors = errors


class NotAuthenticated(DetailError):
    def __init__(
        self, detail: str = NOT_AUTHENTICATED, extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, extra)


class NotFound(DetailError):
    def __init__(self, detail: str = NOT_FOUND) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class UnsupportedMediaType(DetailError):
    def __init__(self, content_type: str) -> None:
        super().__init__(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            UNSUPPORTED_MEDIA_TYPE,
        )
        self.detail = unsupported_media_type(content_type)


async def _detail_error_handler(_request: Request, exc: DetailError) -> JSONResponse:
    body: dict[str, Any] = {"detail": exc.detail, **exc.extra}
    return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)


async def _validation_error_handler(
    _request: Request, exc: ValidationError
) -> JSONResponse:
    return JSONResponse(exc.errors, status_code=exc.status_code)


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return JSONResponse(
            {"detail": method_not_allowed(request.method)},
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        {"detail": _(detail)},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


def field_errors(raw_errors: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Reshape a validation error list into the field mapping clients expect."""
    errors: dict[str, list[str]] = {}
    for error in raw_errors:
        location = [part for part in error["loc"] if part not in ("body", "query")]
        field = str(location[-1]) if location else "non_field_errors"
        if error["type"] == "missing":
            message = _(REQUIRED_FIELD)
        elif error["type"] == "string_too_long":
            message = max_length_error(int(error["ctx"]["max_length"]))
        else:
            message = error["msg"]
        errors.setdefault(field, []).append(message)
    return errors


async def _request_validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        field_errors(exc.errors()), status_code=status.HTTP_400_BAD_REQUEST
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ValidationError, _validation_error_handler)
    app.add_exception_handler(DetailError, _detail_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
