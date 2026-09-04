"""Storing uploaded images below the media root.

Uploads land in a fixed sub directory. A name that is already taken gets a
short random suffix rather than overwriting the existing file, which is how the
project has always stored them. An upload is verified to actually be an image
before it is written, and a stored file is removed from disk when the row that
owned it is deleted or the image is replaced -- both behaviors the original
application had (image field validation and automatic file cleanup).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from wall.config import settings
from wall.exceptions import INVALID_IMAGE, ValidationError
from wall.i18n import _
from wall.security import get_random_string

UPLOAD_TO = "images"
SUFFIX_LENGTH = 7


def _available_name(name: str) -> str:
    """Return ``name``, suffixed until it does not collide with a stored file."""
    directory = settings.media_root / UPLOAD_TO
    stem, extension = Path(name).stem, Path(name).suffix
    candidate = f"{stem}{extension}"
    while (directory / candidate).exists():
        candidate = f"{stem}_{get_random_string(SUFFIX_LENGTH)}{extension}"
    return candidate


def verify_image(upload: UploadFile) -> None:
    """Reject an upload whose content is not a readable image.

    The original image field opened the payload with Pillow and verified it
    before accepting the write; a payload Pillow cannot identify is answered
    with the same field error the framework used to raise.
    """
    try:
        upload.file.seek(0)
        image = Image.open(upload.file)
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError({"image": [str(_(INVALID_IMAGE))]}) from exc
    finally:
        upload.file.seek(0)


def save_image(upload: UploadFile) -> str:
    """Persist ``upload`` and return its name relative to the media root."""
    verify_image(upload)
    directory = settings.media_root / UPLOAD_TO
    directory.mkdir(parents=True, exist_ok=True)
    name = _available_name(Path(upload.filename or "image").name)
    upload.file.seek(0)
    with (directory / name).open("wb") as target:
        shutil.copyfileobj(upload.file, target)
    return f"{UPLOAD_TO}/{name}"


def delete_image(name: str) -> None:
    """Remove a stored image from the media root, ignoring a missing file.

    Mirrors the automatic cleanup the original application performed when a
    row was deleted or its image replaced.
    """
    if not name:
        return
    path = (settings.media_root / name).resolve()
    if settings.media_root.resolve() not in path.parents:
        return
    path.unlink(missing_ok=True)
