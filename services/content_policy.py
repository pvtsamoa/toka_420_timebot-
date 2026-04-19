import os
import re

DEFAULT_BLOCKED_TERMS = ("marijuana",)
_PREFERRED_REPLACEMENTS = {
    "marijuana": "cannabis",
}


def get_blocked_terms() -> list[str]:
    """Load blocked terminology from env, defaulting to project policy."""
    raw = os.getenv("CONTENT_BLOCKLIST_TERMS") or os.getenv("JOKE_BLACKLIST_TERMS") or ",".join(DEFAULT_BLOCKED_TERMS)
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def contains_blocked_term(text: str, blocked_terms: list[str] | None = None) -> bool:
    terms = blocked_terms or get_blocked_terms()
    lowered = (text or "").lower()
    return any(term in lowered for term in terms)


def _replacement_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement.capitalize()
    return replacement


def sanitize_text(text: str) -> str:
    """Replace blocked terminology with preferred wording for outgoing content."""
    value = text or ""
    for bad, good in _PREFERRED_REPLACEMENTS.items():
        pattern = re.compile(rf"\b{re.escape(bad)}\b", re.IGNORECASE)
        value = pattern.sub(lambda m: _replacement_case(m.group(0), good), value)
    return value
