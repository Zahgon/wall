"""Tests for the ad list, create and detail endpoints."""

from __future__ import annotations

import io

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from accounts.models import User
from ads.models import Ad


def generate_photo_file() -> io.BytesIO:
    """Build an in-memory PNG suitable for a multipart upload."""
    file = io.BytesIO()
    image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
    image.save(file, "png")
    file.name = "test.png"
    file.seek(0)
    return file


class TestAdListView:
    def test_get_ads_list(self, app: FastAPI, client: TestClient, ad: Ad) -> None:
        response = client.get(app.url_path_for("ad_list"))

        assert response.status_code == 200


class TestAdDetailView:
    def test_get_ad_detail_authorized(
        self, app: FastAPI, client: TestClient, ad: Ad, user: User, auth: dict[str, str]
    ) -> None:
        response = client.get(app.url_path_for("ad_detail", pk=str(ad.id)), headers=auth)

        assert response.status_code == 200
        assert response.json()["title"] == ad.title

    def test_get_ad_detail_unauthorized(
        self, app: FastAPI, client: TestClient, ad: Ad, user: User
    ) -> None:
        response = client.get(app.url_path_for("ad_detail", pk=str(ad.id)))

        assert response.status_code == 401

    def test_update_ad_authorized(
        self, app: FastAPI, client: TestClient, ad: Ad, user: User, auth: dict[str, str]
    ) -> None:
        response = client.put(
            app.url_path_for("ad_detail", pk=str(ad.id)),
            files={"title": (None, "Fan"), "caption": (None, "Nice")},
            headers=auth,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Fan"

    def test_update_ad_unauthorized(
        self, app: FastAPI, client: TestClient, ad: Ad, user: User
    ) -> None:
        response = client.get(
            app.url_path_for("ad_detail", pk=str(ad.id)), params={"title": "Mic"}
        )

        assert response.status_code == 401

    def test_delete_ad_authorized(
        self, app: FastAPI, client: TestClient, ad: Ad, user: User, auth: dict[str, str]
    ) -> None:
        response = client.delete(app.url_path_for("ad_detail", pk=str(ad.id)), headers=auth)

        assert response.status_code == 204

    def test_delete_ad_unauthorized(
        self, app: FastAPI, client: TestClient, ad: Ad, user: User
    ) -> None:
        response = client.delete(app.url_path_for("ad_detail", pk=str(ad.id)))

        assert response.status_code == 401


class TestAdCreateView:
    def test_create_ad_with_image_authorized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        photo_file = generate_photo_file()

        response = client.post(
            app.url_path_for("ad_create"),
            files={
                "title": (None, "Fan"),
                "caption": (None, "Nice"),
                "image": ("test.png", photo_file, "image/png"),
            },
            headers=auth,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Fan"
        assert response.json()["image"]

    def test_create_ad_without_image_authorized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        response = client.post(
            app.url_path_for("ad_create"),
            files={"title": (None, "Fan"), "caption": (None, "Nice")},
            headers=auth,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Fan"

    def test_create_ad_without_image_unauthorized(
        self, app: FastAPI, client: TestClient, user: User
    ) -> None:
        response = client.post(
            app.url_path_for("ad_create"),
            files={"title": (None, "Fan"), "caption": (None, "Nice")},
        )

        assert response.status_code == 401


class TestAdMessages:
    """The wording of the ad error bodies, asserted literally.

    These strings came from the web framework's own Persian translations in
    the original and are part of the response payload.
    """

    def test_not_found_detail_is_localized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        response = client.get(app.url_path_for("ad_detail", pk=999), headers=auth)

        assert response.status_code == 404
        assert response.json() == {"detail": "یافت نشد."}

    def test_invalid_page_detail_is_localized(self, app: FastAPI, client: TestClient) -> None:
        response = client.get(app.url_path_for("ad_list"), params={"page": 99})

        assert response.status_code == 404
        assert response.json() == {"detail": "صفحه نامعتبر"}

    def test_unsupported_media_type_detail_is_localized(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        response = client.post(
            app.url_path_for("ad_create"), json={"title": "Fan", "caption": "Nice"}, headers=auth
        )

        assert response.status_code == 415
        assert response.json() == {
            "detail": "نوع رسانه application/json در درخواست پشتیبانی نمیشود."
        }


class TestAdFileLifecycle:
    """The image file on disk follows the ad row, as it did in the original.

    The original deleted the backing file when the row was deleted and when
    the image was replaced; uploads that are not real images were rejected
    before anything touched the disk.
    """

    def _create_ad(self, app: FastAPI, client: TestClient, auth: dict[str, str]) -> dict:
        response = client.post(
            app.url_path_for("ad_create"),
            files={
                "title": (None, "Fan"),
                "caption": (None, "Nice"),
                "image": ("test.png", generate_photo_file(), "image/png"),
            },
            headers=auth,
        )
        assert response.status_code == 200
        return response.json()

    def _stored_path(self, payload: dict):
        from wall.config import settings

        name = payload["image"].removeprefix(settings.media_url)
        return settings.media_root / name

    def test_delete_removes_image_file_from_disk(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        payload = self._create_ad(app, client, auth)
        path = self._stored_path(payload)
        assert path.is_file()

        response = client.delete(app.url_path_for("ad_detail", pk=str(payload["id"])), headers=auth)

        assert response.status_code == 204
        assert not path.exists()

    def test_replacing_image_removes_superseded_file(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        payload = self._create_ad(app, client, auth)
        old_path = self._stored_path(payload)
        assert old_path.is_file()

        response = client.put(
            app.url_path_for("ad_detail", pk=str(payload["id"])),
            files={
                "title": (None, "Fan"),
                "caption": (None, "Nice"),
                "image": ("test.png", generate_photo_file(), "image/png"),
            },
            headers=auth,
        )

        assert response.status_code == 200
        new_path = self._stored_path(response.json())
        assert new_path.is_file()
        assert new_path != old_path
        assert not old_path.exists()

    def test_non_image_upload_is_rejected_and_not_saved(
        self, app: FastAPI, client: TestClient, user: User, auth: dict[str, str]
    ) -> None:
        from wall.config import settings

        images_dir = settings.media_root / "images"
        before = set(images_dir.iterdir()) if images_dir.is_dir() else set()

        response = client.post(
            app.url_path_for("ad_create"),
            files={
                "title": (None, "Fan"),
                "caption": (None, "Nice"),
                "image": ("evil.png", io.BytesIO(b"not an image at all"), "image/png"),
            },
            headers=auth,
        )

        assert response.status_code == 400
        assert response.json() == {
            "image": ["یک عکس معتبر آپلود کنید. فایلی که ارسال کردید عکس یا عکس خراب شده نیست"]
        }
        after = set(images_dir.iterdir()) if images_dir.is_dir() else set()
        assert after == before
