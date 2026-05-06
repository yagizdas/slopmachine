from __future__ import annotations

import re
import secrets


def clamp_int(value: int | float | None, default: int, minimum: int, maximum: int) -> int:
    if value is None:
        return default

    try:
        number = round(float(value))
    except (TypeError, ValueError):
        return default

    return max(minimum, min(maximum, number))


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:72] or f"slop-{secrets.token_hex(4)}"
