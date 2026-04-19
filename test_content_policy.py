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


def test_jokes_file_still_parses():
    jokes_path = Path(__file__).resolve().parent / "media" / "jokes.json"
    payload = json.loads(jokes_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert all(isinstance(item, str) for item in payload)
