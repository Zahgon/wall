"""Translation helpers bound to the project's ``locale/`` directory.

Two catalogues live side by side there. The one that shipped with the project
is reused as-is - same directory layout, same domain, same language - and has
no compiled form, so gettext falls back to returning the message id, which is
exactly what the project did before. The second holds the error strings that
the web framework layer used to supply from its own translations; they are
vendored here so those responses keep their original wording.
"""

from __future__ import annotations

import gettext as _gettext

from wall.config import settings

_languages = [settings.language, settings.language_code.split("-")[0]]


def _catalogue(domain: str) -> _gettext.NullTranslations:
    return _gettext.translation(
        domain,
        localedir=str(settings.locale_dir),
        languages=_languages,
        fallback=True,
    )


_project = _catalogue(settings.translation_domain)
_api = _catalogue(settings.api_translation_domain)


def gettext_lazy(message: str) -> str:
    """Translate ``message``, preferring the API catalogue."""
    translated = _api.gettext(message)
    if translated != message:
        return translated
    return _project.gettext(message)


_ = gettext_lazy
