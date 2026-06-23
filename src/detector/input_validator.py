"""
Input validation and error handling for CCD detection pipeline.

All public detector methods should validate inputs here before processing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Raised when interaction data fails validation."""
    pass


REQUIRED_INTERACTION_FIELDS = ("user_prompt", "agent_response")
OPTIONAL_INTERACTION_FIELDS = {
    "turn_id": int,
    "timestamp": str,
    "artifacts_generated": list,
    "is_challenge": bool,
    "admission_type": (str, type(None)),
    "component_claims": list,
}


def validate_interaction(interaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize a single interaction dict.

    - Ensures required fields are present and non-empty strings.
    - Adds defaults for optional missing fields.
    - Raises ValidationError on unrecoverable bad input.
    - Returns a clean, normalized copy.
    """
    if not isinstance(interaction, dict):
        raise ValidationError(f"Interaction must be a dict, got {type(interaction).__name__}")

    clean = dict(interaction)

    for field in REQUIRED_INTERACTION_FIELDS:
        if field not in clean:
            raise ValidationError(f"Interaction missing required field: '{field}'")
        if not isinstance(clean[field], str):
            # Coerce to string with a warning rather than crash
            logger.warning("Field '%s' is not a string (got %s), coercing", field, type(clean[field]).__name__)
            clean[field] = str(clean[field])

    # Defaults for optional fields
    clean.setdefault("turn_id", 0)
    clean.setdefault("timestamp", "")
    clean.setdefault("artifacts_generated", [])
    clean.setdefault("is_challenge", False)
    clean.setdefault("admission_type", None)
    clean.setdefault("component_claims", [])

    return clean


def validate_interactions(interactions: Any) -> List[Dict[str, Any]]:
    """
    Validate a list of interactions. Returns cleaned list.
    Empty list is valid (returns []).
    Non-list input raises ValidationError.
    Individual malformed items are logged and skipped (graceful degradation).
    """
    if not isinstance(interactions, list):
        raise ValidationError(f"interactions must be a list, got {type(interactions).__name__}")

    cleaned = []
    for idx, item in enumerate(interactions):
        try:
            cleaned.append(validate_interaction(item))
        except ValidationError as exc:
            logger.warning("Skipping malformed interaction at index %d: %s", idx, exc)
    return cleaned


def validate_component_name(component_name: Any) -> str:
    """Coerce and validate component_name to a non-empty string."""
    if component_name is None:
        raise ValidationError("component_name must not be None")
    name = str(component_name).strip()
    if not name:
        raise ValidationError("component_name must not be empty")
    return name


def validate_confidence(value: Any) -> float:
    """Clamp confidence to [0.0, 1.0]."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"confidence must be numeric, got {value!r}")
    return max(0.0, min(1.0, f))
