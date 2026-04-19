import datetime as dt
import json
from pathlib import Path

from services.joke_rotation import JokeRotationStore


def _make_store(tmp_path: Path, jokes: list[str]) -> JokeRotationStore:
    jokes_path = tmp_path / "jokes.json"
    jokes_path.write_text(json.dumps(jokes), encoding="utf-8")
    db_path = tmp_path / "jokes.db"
    return JokeRotationStore(db_path=str(db_path), jokes_path=str(jokes_path))


def test_joke_ingest_deduplicates_by_fingerprint(tmp_path):

    store = _make_store(tmp_path, ["Same line", "Same  line", "Different line"])

    inserted = store.refresh_inventory()
    assert inserted == 2

    # Re-ingest should not duplicate rows.
    inserted_again = store.refresh_inventory()
    assert inserted_again == 0


def test_build_rotation_assigns_window(tmp_path):

    jokes = [f"Weedcoin OG joke line number {i}" for i in range(1, 30)]
    store = _make_store(tmp_path, jokes)
    store.refresh_inventory()

    assigned = store.build_rotation(days=15)
    assert assigned == 15

    # Calling again should not reassign existing days.
    assigned_again = store.build_rotation(days=15)
    assert assigned_again == 0


def test_get_today_joke_uses_local_fallback(tmp_path):

    store = _make_store(tmp_path, ["Fallback A", "Fallback B"])

    # No external source URLs set, should still work via local fallback seed.
    joke = store.get_today_joke(now_utc=dt.datetime(2026, 3, 13, tzinfo=dt.timezone.utc))
    assert joke in {"Fallback A", "Fallback B"}



def test_blacklist_term_marijuana_is_filtered(tmp_path):

    store = _make_store(tmp_path, ["This line has marijuana reference", "Clean joke line here"])

    inserted = store.refresh_inventory()
    assert inserted == 2

    joke = store.get_today_joke(now_utc=dt.datetime(2026, 3, 13, tzinfo=dt.timezone.utc))
    assert "marijuana" not in joke.lower()
