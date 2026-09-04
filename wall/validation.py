"""Body validation.

Bodies are parsed by hand so that a single endpoint can accept more than one
encoding, which means the schemas have to be applied explicitly. Failures are
translated into the field-to-messages mapping the API answers with.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from wall.exceptions import ValidationError, field_errors

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def validate(schema: type[SchemaT], data: dict[str, Any]) -> SchemaT:
    """Validate ``data`` against ``schema`` or raise a field level failure."""
    try:
        return schema.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(field_errors(exc.errors())) from None
