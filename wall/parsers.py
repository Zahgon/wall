"""Request body parsing.

Two policies exist in this project. Most endpoints accept whatever the client
sends -- JSON or an HTML form -- while the endpoints that receive an upload
accept only a multipart form and reject anything else. Both policies normalise
the body into a plain mapping so the schemas can validate it.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import Request

from wall.exceptions import UnsupportedMediaType

JSON_MEDIA_TYPE = "application/json"
MULTIPART_MEDIA_TYPE = "multipart/form-data"
URLENCODED_MEDIA_TYPE = "application/x-www-form-urlencoded"

FORM_MEDIA_TYPES = (MULTIPART_MEDIA_TYPE, URLENCODED_MEDIA_TYPE)


def media_type(request: Request) -> str:
    return (request.headers.get("content-type") or "").split(";")[0].strip().lower()


async def _parse_json(request: Request) -> dict[str, Any]:
    body = await request.body()
    if not body:
        return {}
    try:
        payload = json.loads(body)
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


async def _parse_form(request: Request) -> dict[str, Any]:
    form = await request.form()
    return dict(form)


async def parse_data(request: Request) -> dict[str, Any]:
    """Accept JSON or form encoded bodies, mirroring the default parser set."""
    content_type = media_type(request)
    if not content_type:
        return {}
    if content_type == JSON_MEDIA_TYPE:
        return await _parse_json(request)
    if content_type in FORM_MEDIA_TYPES:
        return await _parse_form(request)
    raise UnsupportedMediaType(content_type)


async def parse_multipart(request: Request) -> dict[str, Any]:
    """Accept only multipart form bodies; anything else is unsupported."""
    content_type = media_type(request)
    if content_type != MULTIPART_MEDIA_TYPE:
        raise UnsupportedMediaType(content_type)
    return await _parse_form(request)
