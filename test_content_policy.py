import json
from pathlib import Path

from services.content_policy import contains_blocked_term, sanitize_text


def test_sanitize_text_replaces_marijuana_with_cannabis():
    text = "Marijuana is a flower and marijuana grows naturally."
    cleaned = sanitize_text(text)
    assert "marijuana" not in cleaned.lower()
    assert "cannabis" in cleaned.lower()


def test_media_json_does_not_ship_blocked_term():
    media_dir = Path(__file__).resolve().parent / "media"
    offenders = []

    for path in media_dir.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        if contains_blocked_term(text):
            offenders.append(path.name)

    assert not offenders, f"Blocked terminology remains in media files: {offenders}"


def test_quotes_file_still_parses_after_policy_cleanup():
    quotes_path = Path(__file__).resolve().parent / "media" / "cannabis_quotes.json"
    payload = json.loads(quotes_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert all("quote" in item and "source" in item for item in payload)
