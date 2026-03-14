import datetime as dt
import json
from pathlib import Path
from unittest.mock import Mock, patch

from services.joke_rotation import JokeRotationStore


def _make_store(tmp_path: Path, jokes: list[str]) -> JokeRotationStore:
    jokes_path = tmp_path / "jokes.json"
    jokes_path.write_text(json.dumps(jokes), encoding="utf-8")
    db_path = tmp_path / "jokes.db"
    return JokeRotationStore(db_path=str(db_path), jokes_path=str(jokes_path))


def test_joke_ingest_deduplicates_by_fingerprint(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKE_REDDIT_FEEDS", "off")
    monkeypatch.setenv("WEEDCOINOG_X_ACCOUNT_URL", "off")
    monkeypatch.setenv("WEEDCOINOG_X_COMMUNITY_URL", "off")
    store = _make_store(tmp_path, ["Same line", "Same  line", "Different line"])

    inserted = store.refresh_inventory()
    assert inserted == 2

    # Re-ingest should not duplicate rows.
    inserted_again = store.refresh_inventory()
    assert inserted_again == 0


def test_build_rotation_assigns_window(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKE_REDDIT_FEEDS", "off")
    monkeypatch.setenv("WEEDCOINOG_X_ACCOUNT_URL", "off")
    monkeypatch.setenv("WEEDCOINOG_X_COMMUNITY_URL", "off")
    jokes = [f"Weedcoin OG joke line number {i}" for i in range(1, 30)]
    store = _make_store(tmp_path, jokes)
    store.refresh_inventory()

    assigned = store.build_rotation(days=15)
    assert assigned == 15

    # Calling again should not reassign existing days.
    assigned_again = store.build_rotation(days=15)
    assert assigned_again == 0


def test_get_today_joke_uses_local_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKE_REDDIT_FEEDS", "off")
    monkeypatch.setenv("WEEDCOINOG_X_ACCOUNT_URL", "off")
    monkeypatch.setenv("WEEDCOINOG_X_COMMUNITY_URL", "off")
    store = _make_store(tmp_path, ["Fallback A", "Fallback B"])

    # No external source URLs set, should still work via local fallback seed.
    joke = store.get_today_joke(now_utc=dt.datetime(2026, 3, 13, tzinfo=dt.timezone.utc))
    assert joke in {"Fallback A", "Fallback B"}


def test_reddit_json_source_extracts_titles(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKE_REDDIT_FEEDS", "off")
    monkeypatch.setenv("WEEDCOINOG_X_ACCOUNT_URL", "off")
    monkeypatch.setenv("WEEDCOINOG_X_COMMUNITY_URL", "off")
    store = _make_store(tmp_path, ["Seed fallback line"])

    payload = {
        "data": {
            "children": [
                {"data": {"title": "Funny one", "selftext": "Body text"}},
                {"data": {"title": "Another joke", "selftext": ""}},
            ]
        }
    }

    fake_response = Mock()
    fake_response.headers = {"Content-Type": "application/json"}
    fake_response.json.return_value = payload
    fake_response.text = ""
    fake_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=fake_response):
        rows = store._fetch_external_source("https://www.reddit.com/r/Jokes/new.json?limit=2")

    assert "Funny one - Body text" in rows
    assert "Another joke" in rows


def test_blacklist_term_marijuana_is_filtered(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKE_REDDIT_FEEDS", "off")
    monkeypatch.setenv("WEEDCOINOG_X_ACCOUNT_URL", "off")
    monkeypatch.setenv("WEEDCOINOG_X_COMMUNITY_URL", "off")
    store = _make_store(tmp_path, ["This line has marijuana reference", "Clean joke line here"])

    inserted = store.refresh_inventory()
    assert inserted == 2

    joke = store.get_today_joke(now_utc=dt.datetime(2026, 3, 13, tzinfo=dt.timezone.utc))
    assert "marijuana" not in joke.lower()
