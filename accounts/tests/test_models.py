"""Tests for the user model."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from accounts.models import User
from wall.i18n import gettext_lazy as _


class TestAuthorModel:
    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session) -> None:
        self.user = User(username="Kami")
        db_session.add(self.user)
        db_session.commit()
        db_session.refresh(self.user)

    def test_username_label(self) -> None:
        field_label = User.verbose_name_of("username")
        assert field_label == _("username")

    def test_object_name_is_last_name_comma_first_name(self) -> None:
        expected_object_name = f"{self.user.username}"
        assert expected_object_name == str(self.user)

    def test_str_method(self) -> None:
        assert self.user.__str__() == self.user.username
