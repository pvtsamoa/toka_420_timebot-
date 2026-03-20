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


@pytest.mark.parametrize(
    "signature",
    ["ðŸ", "âš", "â", "Â±", "âœ", "ï¸", "â†'", "â€"", "â€¢", "â"€", "â€""],
)
def test_python_sources_do_not_contain_mojibake(signature):
    """Prevent common UTF-8/Windows-1252 corruption patterns in source files."""
    root = Path(__file__).resolve().parent
    offenders = []
    this_file = Path(__file__).name

    for py_file in root.rglob("*.py"):
        if py_file.name == this_file:
            continue
        text = py_file.read_text(encoding="utf-8")
        if signature in text:
            offenders.append(str(py_file.relative_to(root)))

    assert not offenders, f"Found mojibake signature {signature!r} in: {offenders}"


def test_validate_config_rejects_invalid_tz(monkeypatch):
    """Invalid TZ values should fail fast before scheduler startup."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("TELEGRAM_GLOBAL_CHAT_ID", "123456")
    monkeypatch.setenv("TZ", "Mars/Phobos")

    with pytest.raises(ValueError, match="Invalid TZ value"):
        validate_config()
