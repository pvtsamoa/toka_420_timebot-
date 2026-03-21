"""Regression tests for config loading, encoding integrity, and timezone validation."""

from pathlib import Path

import pytest

from config import get_settings
from services.config_validator import validate_config


def test_settings_are_read_at_call_time(monkeypatch):
    """Config values should reflect the latest environment at call time."""
    monkeypatch.setenv("WEEDCOIN_TOKEN", "weedcoin-test")
    assert get_settings().WEEDCOIN_TOKEN == "weedcoin-test"

    monkeypatch.setenv("SECONDARY_TOKEN", "solana")
    assert get_settings().SECONDARY_TOKEN == "solana"


def test_python_sources_are_clean_utf8():
    """All source files must be valid UTF-8 with no replacement characters."""
    root = Path(__file__).resolve().parent
    bad_encoding = []
    replacement_char = "\ufffd"

    for py_file in root.rglob("*.py"):
        if any(part.startswith(".venv") for part in py_file.parts):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad_encoding.append(str(py_file.relative_to(root)))
            continue
        if replacement_char in text:
            bad_encoding.append(str(py_file.relative_to(root)) + " (replacement char)")

    assert not bad_encoding, f"Encoding problems in: {bad_encoding}"


def test_validate_config_rejects_invalid_tz(monkeypatch):
    """Invalid TZ values should fail fast before scheduler startup."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("TELEGRAM_GLOBAL_CHAT_ID", "123456")
    monkeypatch.setenv("TZ", "Mars/Phobos")

    with pytest.raises(ValueError, match="Invalid TZ value"):
        validate_config()
