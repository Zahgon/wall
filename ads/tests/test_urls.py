"""Tests that the ads paths reach the expected handlers."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

from ads import routes
from ads.models import Ad


class TestUrls:
    def test_ad_list_url(
        self, app: FastAPI, route_named: Callable[[APIRouter, str], APIRoute]
    ) -> None:
        assert app.url_path_for("ad_list") == "/api/ads/all"

        route = route_named(routes.router, "ad_list")
        assert route.endpoint is routes.ad_list
        assert route.methods == {"GET"}

    def test_ad_create_url(
        self, app: FastAPI, route_named: Callable[[APIRouter, str], APIRoute]
    ) -> None:
        assert app.url_path_for("ad_create") == "/api/ads/add"

        route = route_named(routes.router, "ad_create")
        assert route.endpoint is routes.ad_create
        assert route.methods == {"POST"}

    def test_ad_detail_url(
        self, app: FastAPI, ad: Ad, route_named: Callable[[APIRouter, str], APIRoute]
    ) -> None:
        assert app.url_path_for("ad_detail", pk=str(ad.id)) == f"/api/ads/{ad.id}"

        route = route_named(routes.router, "ad_detail")
        assert route.endpoint is routes.ad_detail
        assert route.methods == {"GET", "PUT", "DELETE"}
