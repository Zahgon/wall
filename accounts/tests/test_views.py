"""Tests for the profile and login endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from accounts.models import User

USERNAME = "amir"
PASSWORD = "test1234"


class TestUserView:
    def test_profile_detail_authorized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        response = client.get(app.url_path_for("profile_view"), headers=auth)

        assert response.status_code == 200
        assert response.json()["username"]
        assert response.json() == {"username": USERNAME}

    def test_profile_detail_unauthorized(self, app: FastAPI, client: TestClient, user: User) -> None:
        response = client.get(app.url_path_for("profile_view"))

        assert response.status_code == 401

    def test_profile_update_authorized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        response = client.put(
            app.url_path_for("profile_view"), data={"username": "Karim"}, headers=auth
        )

        assert response.status_code == 200

    def test_profile_update_unauthorized(self, app: FastAPI, client: TestClient, user: User) -> None:
        response = client.put(app.url_path_for("profile_view"), data={"username": "Karim"})

        assert response.status_code == 401

    def test_login(self, app: FastAPI, client: TestClient, user: User) -> None:
        response = client.post(
            app.url_path_for("login"), data={"username": USERNAME, "password": PASSWORD}
        )

        assert response.status_code == 200
        assert response.json()["access"]


class TestUserViewMessages:
    """The wording of the error bodies, not just their status codes.

    The original served these strings from the web framework's own Persian
    translations; they are part of the response payload and clients may show
    them, so they are asserted literally.
    """

    def test_unauthorized_detail_is_localized(self, app: FastAPI, client: TestClient) -> None:
        response = client.get(app.url_path_for("profile_view"))

        assert response.json() == {"detail": "اطلاعات برای اعتبارسنجی ارسال نشده است."}

    def test_method_not_allowed_detail_is_localized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        response = client.post(app.url_path_for("profile_view"), headers=auth)

        assert response.status_code == 405
        assert response.json() == {"detail": 'متد POST مجاز نیست.'}

    def test_required_field_detail_is_localized(self, app: FastAPI, client: TestClient) -> None:
        response = client.post(app.url_path_for("login"), json={})

        assert response.status_code == 400
        assert response.json() == {
            "username": ["این مقدار لازم است."],
            "password": ["این مقدار لازم است."],
        }

    def test_credentials_detail_stays_untranslated(
        self, app: FastAPI, client: TestClient, user: User
    ) -> None:
        """This one had no translation originally and must not gain one."""
        response = client.post(
            app.url_path_for("login"), data={"username": USERNAME, "password": "wrong"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "No active account found with the given credentials"}
