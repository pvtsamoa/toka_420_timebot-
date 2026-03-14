"""Regression tests for config loading, message safety, encoding integrity, and timezone validation."""

from pathlib import Path

import pytest

from config import get_settings
from commands.news import _build_news_message
from services.config_validator import validate_config


def test_settings_are_read_at_call_time(monkeypatch):
    """Config values should reflect latest environment values."""
    monkeypatch.setenv("TELEGRAM_SCOPE", "apac")
    assert get_settings().TELEGRAM_SCOPE == "apac"

    monkeypatch.setenv("TELEGRAM_SCOPE", "emea")
    assert get_settings().TELEGRAM_SCOPE == "emea"


def test_news_message_builder_escapes_dynamic_fields():
    """Dynamic RSS values should be escaped for Telegram HTML parse mode."""
    message = _build_news_message(
        category_emoji="$",
        section_title="Markets <Now>",
        article_title="A_[b](c) & <d>",
        source="Feed & Wire",
        link="https://example.com/news?a=1&b=2",
    )

    assert "<b>Markets &lt;Now&gt;</b>" in message
    assert "A_[b](c) &amp; &lt;d&gt;" in message
    assert "Source: Feed &amp; Wire" in message
    assert "href=\"https://example.com/news?a=1&amp;b=2\"" in message


@pytest.mark.parametrize(
    "signature",
    ["ðŸ", "âš", "â", "Â±", "âœ", "ï¸", "â†’", "â€”", "â€¢", "â”€", "â€“"],
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
    monkeypatch.setenv("TELEGRAM_SCOPE", "all")
    monkeypatch.setenv("TZ", "Mars/Phobos")

    with pytest.raises(ValueError, match="Invalid TZ value"):
        validate_config()
