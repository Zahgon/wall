"""Page-number pagination mirroring the original list envelope."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from starlette.requests import Request

from wall.exceptions import INVALID_PAGE, NotFound

T = TypeVar("T")

PAGE_QUERY_PARAM = "page"


def _positive_int(value: str, cutoff: int | None = None) -> int:
    """Parse a strictly positive integer, clamped to ``cutoff``."""
    number = int(value)
    if number <= 0:
        raise ValueError("expected a positive integer")
    if cutoff is not None:
        return min(number, cutoff)
    return number


def _replace_query_param(url: str, key: str, value: object) -> str:
    scheme, netloc, path, query, fragment = urlsplit(url)
    params = [(name, item) for name, item in parse_qsl(query, keep_blank_values=True) if name != key]
    params.append((key, str(value)))
    return urlunsplit((scheme, netloc, path, urlencode(params), fragment))


def _remove_query_param(url: str, key: str) -> str:
    scheme, netloc, path, query, fragment = urlsplit(url)
    params = [(name, item) for name, item in parse_qsl(query, keep_blank_values=True) if name != key]
    return urlunsplit((scheme, netloc, path, urlencode(params), fragment))


@dataclass(slots=True)
class Page:
    """A slice of a result set plus the links that surround it."""

    objects: list
    count: int
    next: str | None
    previous: str | None


class StandardResultsSetPagination:
    """One object per page by default, overridable up to a hard ceiling."""

    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_page_size(self, request: Request) -> int:
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return self.page_size
        try:
            return _positive_int(raw, cutoff=self.max_page_size)
        except (TypeError, ValueError):
            return self.page_size

    def get_page_number(self, request: Request, total_pages: int) -> int:
        raw = request.query_params.get(PAGE_QUERY_PARAM, "1")
        if raw == "last":
            return total_pages
        try:
            return _positive_int(raw)
        except (TypeError, ValueError):
            raise NotFound(INVALID_PAGE) from None

    def paginate(self, queryset: Sequence[T], request: Request) -> Page:
        """Slice ``queryset`` for the requested page.

        An empty result set still has a valid first page; any other page beyond
        the end is a 404, exactly as the original paginator reported it.
        """
        page_size = self.get_page_size(request)
        count = len(queryset)
        total_pages = max(1, math.ceil(count / page_size))
        number = self.get_page_number(request, total_pages)
        if number > total_pages:
            raise NotFound(INVALID_PAGE)

        start = (number - 1) * page_size
        url = str(request.url)
        following = _replace_query_param(url, PAGE_QUERY_PARAM, number + 1) if number < total_pages else None
        if number <= 1:
            preceding = None
        elif number == 2:
            preceding = _remove_query_param(url, PAGE_QUERY_PARAM)
        else:
            preceding = _replace_query_param(url, PAGE_QUERY_PARAM, number - 1)

        return Page(
            objects=list(queryset[start : start + page_size]),
            count=count,
            next=following,
            previous=preceding,
        )
