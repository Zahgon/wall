"""Tests for the ad model."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from accounts.managers import UserManager
from ads.models import Ad
from wall.i18n import gettext_lazy as _


class TestAuthorModel:
    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session) -> None:
        self.user = UserManager(db_session).create_user(username="Pedi")
        self.ad = Ad(title="Iphone", caption="nice", publisher=self.user)
        db_session.add(self.ad)
        db_session.commit()
        db_session.refresh(self.ad)

    def test_title_label(self) -> None:
        field_label = Ad.verbose_name_of("title")
        assert field_label == _("title")

    def test_caption_label(self) -> None:
        field_label = Ad.verbose_name_of("caption")
        assert field_label == _("caption")

    def test_image_label(self) -> None:
        field_label = Ad.verbose_name_of("image")
        assert field_label == _("image")

    def test_str_method(self) -> None:
        assert self.ad.__str__() == self.ad.title
