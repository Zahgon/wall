"""Tests for the settings module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wall.config import Settings


class TestSecretKey:
    def test_debug_defaults_to_a_random_key(self) -> None:
        settings = Settings(_env_file=None)

        assert settings.debug is True
        assert settings.secret_key

    def test_non_debug_without_key_refuses_to_boot(self) -> None:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, debug=False)

    def test_non_debug_with_key_boots(self) -> None:
        settings = Settings(_env_file=None, debug=False, secret_key="stable-key")

        assert settings.secret_key == "stable-key"
