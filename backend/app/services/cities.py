"""Deterministic city-name normalization, so "ft. lauderdale" and "Fort Lauderdale" are the same city."""

import re

ALIASES: dict[str, str] = {
    "ft lauderdale": "Fort Lauderdale",
    "ft. lauderdale": "Fort Lauderdale",
    "fort-lauderdale": "Fort Lauderdale",
    "jax": "Jacksonville",
}


def normalize_city(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name).strip()
    alias = ALIASES.get(collapsed.lower())
    if alias:
        return alias
    if collapsed.islower() or collapsed.isupper():
        return " ".join(word.capitalize() for word in collapsed.split(" "))
    return collapsed  # mixed case was typed on purpose ("McAllen")
