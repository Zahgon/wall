"""Tests that the accounts paths reach the expected handlers."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

from accounts import routes


class TestUrls:
    def test_login(
        self, app: FastAPI, route_named: Callable[[APIRouter, str], APIRoute]
    ) -> None:
        assert app.url_path_for("login") == "/api/accounts/login"

        route = route_named(routes.router, "login")
        assert route.endpoint is routes.login
        assert route.methods == {"POST"}

    def test_profile_detail(
        self, app: FastAPI, route_named: Callable[[APIRouter, str], APIRoute]
    ) -> None:
        assert app.url_path_for("profile_view") == "/api/accounts/profile"

        route = route_named(routes.router, "profile_view")
        assert route.endpoint is routes.profile_view
        assert route.methods == {"GET", "PUT"}
