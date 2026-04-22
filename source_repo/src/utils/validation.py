"""Input validation utilities."""
from typing import Any


def validate_payload(payload: dict[str, Any], required_keys: list[str]) -> list[str]:
    errors = []
    if not isinstance(payload, dict):
        return ["Payload must be a dictionary"]
    for key in required_keys:
        if key not in payload:
            errors.append(f"Missing required key: {key}")
    return errors


def validate_priority(priority: int) -> bool:
    return isinstance(priority, int) and 0 <= priority <= 10


def validate_job_name(name: str) -> list[str]:
    errors = []
    if not name or not isinstance(name, str):
        errors.append("Job name must be a non-empty string")
    elif len(name) > 256:
        errors.append("Job name must be 256 characters or fewer")
    elif not name.replace("_", "").replace("-", "").replace(".", "").isalnum():
        errors.append("Job name must contain only alphanumeric characters, hyphens, underscores, and dots")
    return errors


def sanitize_tags(tags: list[str]) -> list[str]:
    seen = set()
    result = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result