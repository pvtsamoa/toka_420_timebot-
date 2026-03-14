from unittest.mock import Mock, patch
from types import SimpleNamespace

from services import x_poster
from services.x_poster import format_for_x, post_mirror


def test_format_for_x_collapses_whitespace_and_trims():
    raw = "Line one\n\n  line   two\tline three"
    cleaned = format_for_x(raw, max_chars=20)
    assert "\n" not in cleaned
    assert "  " not in cleaned
    assert len(cleaned) <= 20


def test_post_mirror_returns_false_when_disabled(monkeypatch):
    monkeypatch.setenv("X_POST_ENABLED", "false")
    assert post_mirror("hello world") is False


def test_post_mirror_returns_false_when_missing_creds(monkeypatch):
    monkeypatch.setenv("X_POST_ENABLED", "true")
    monkeypatch.delenv("X_API_KEY", raising=False)
    monkeypatch.delenv("X_API_SECRET", raising=False)
    monkeypatch.delenv("X_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("X_ACCESS_TOKEN_SECRET", raising=False)

    assert post_mirror("hello world") is False


def test_post_mirror_retries_transient_503_and_succeeds(monkeypatch):
    monkeypatch.setenv("X_POST_ENABLED", "true")
    monkeypatch.setenv("X_API_KEY", "k")
    monkeypatch.setenv("X_API_SECRET", "s")
    monkeypatch.setenv("X_ACCESS_TOKEN", "t")
    monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "ts")
    monkeypatch.setenv("X_POST_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("X_POST_RETRY_DELAY_SECONDS", "0.01")

    fail = Mock(status_code=503, text='{"status":503}')
    ok = Mock(status_code=201, text='{"data":{"id":"1"}}')

    fake_oauth_module = SimpleNamespace(OAuth1=lambda *args, **kwargs: object())

    with patch.dict("sys.modules", {"requests_oauthlib": fake_oauth_module}):
        with patch("services.x_poster.time.sleep"):
            with patch("requests.post", side_effect=[fail, ok]) as mocked_post:
                assert post_mirror("retry me") is True
                assert mocked_post.call_count == 2


def test_failed_post_does_not_block_immediate_retry(monkeypatch):
    monkeypatch.setenv("X_POST_ENABLED", "true")
    monkeypatch.setenv("X_API_KEY", "k")
    monkeypatch.setenv("X_API_SECRET", "s")
    monkeypatch.setenv("X_ACCESS_TOKEN", "t")
    monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "ts")
    monkeypatch.setenv("X_POST_MAX_ATTEMPTS", "1")

    # Reset duplicate state for deterministic behavior.
    x_poster._LAST_POST["fingerprint"] = None
    x_poster._LAST_POST["ts"] = 0.0

    fail = Mock(status_code=503, text='{"status":503}')
    ok = Mock(status_code=201, text='{"data":{"id":"1"}}')

    fake_oauth_module = SimpleNamespace(OAuth1=lambda *args, **kwargs: object())

    with patch.dict("sys.modules", {"requests_oauthlib": fake_oauth_module}):
        with patch("requests.post", return_value=fail):
            assert post_mirror("same message") is False
        with patch("requests.post", return_value=ok):
            assert post_mirror("same message") is True
