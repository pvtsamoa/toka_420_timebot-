import datetime as dt
import hashlib
import json
import logging
import os
import random
import sqlite3
import threading
from typing import Iterable

from services.content_policy import sanitize_text

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "jokes.db")
DEFAULT_JOKES_PATH = os.path.join(PROJECT_ROOT, "media", "jokes.json")
ROTATION_DAYS = 15


class JokeRotationStore:
    """Persistent 15-day joke rotation backed by SQLite and a local jokes.json seed."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, jokes_path: str = DEFAULT_JOKES_PATH):
        self.db_path = db_path
        self.jokes_path = jokes_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jokes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    body TEXT NOT NULL,
                    source TEXT NOT NULL,
                    fingerprint TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    use_count INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS joke_rotation (
                    day_key TEXT PRIMARY KEY,
                    joke_id INTEGER NOT NULL,
                    assigned_at TEXT NOT NULL,
                    sent_at TEXT,
                    FOREIGN KEY (joke_id) REFERENCES jokes(id)
                )
                """
            )
            conn.commit()

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join((text or "").strip().split())

    @staticmethod
    def _fingerprint(text: str) -> str:
        normalized = JokeRotationStore._normalize_text(text).lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _is_candidate_safe(self, text: str) -> bool:
        t = (text or "").lower()
        if len(t) < 8 or len(t) > 400:
            return False
        blocked = [
            "seed phrase", "wallet connect", "walletconnect",
            "send me your", "airdrop link", "guaranteed profit",
        ]
        return not any(term in t for term in blocked)

    def _insert_candidates(self, candidates: Iterable[str], source: str) -> int:
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        inserted = 0
        with self._connect() as conn:
            for raw in candidates:
                body = sanitize_text(self._normalize_text(raw))
                if not body or not self._is_candidate_safe(body):
                    continue
                fp = self._fingerprint(body)
                try:
                    conn.execute(
                        "INSERT INTO jokes (body, source, fingerprint, created_at) VALUES (?, ?, ?, ?)",
                        (body, source, fp, now),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    continue
            conn.commit()
        return inserted

    def _load_local_jokes(self) -> list[str]:
        try:
            with open(self.jokes_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(item) for item in data if isinstance(item, str)]
        except Exception as e:
            logger.warning("Could not load local jokes: %s", e)
        return []

    def refresh_inventory(self) -> int:
        """Load jokes from the local jokes.json seed file into the DB."""
        inserted = self._insert_candidates(self._load_local_jokes(), "local")
        logger.info("Joke inventory refreshed: %d new entries", inserted)
        return inserted

    def _count_active(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM jokes WHERE active = 1").fetchone()
            return int(row["c"] if row else 0)

    def ensure_inventory(self, min_count: int = 15) -> None:
        if self._count_active() < min_count:
            self.refresh_inventory()

    def build_rotation(self, days: int = ROTATION_DAYS, start_date: dt.date | None = None) -> int:
        """Assign jokes for missing day keys over a rolling window."""
        self.ensure_inventory(min_count=days)
        start_date = start_date or dt.datetime.now(dt.timezone.utc).date()
        assigned = 0

        with self._connect() as conn:
            existing_rows = conn.execute(
                "SELECT day_key, joke_id FROM joke_rotation WHERE day_key >= ? AND day_key <= ?",
                (
                    start_date.isoformat(),
                    (start_date + dt.timedelta(days=days - 1)).isoformat(),
                ),
            ).fetchall()

            used_ids = {int(r["joke_id"]) for r in existing_rows}
            now = dt.datetime.now(dt.timezone.utc).isoformat()

            for offset in range(days):
                day_key = (start_date + dt.timedelta(days=offset)).isoformat()
                if conn.execute(
                    "SELECT joke_id FROM joke_rotation WHERE day_key = ?", (day_key,)
                ).fetchone():
                    continue

                candidates = conn.execute(
                    "SELECT id FROM jokes WHERE active = 1 ORDER BY use_count ASC, COALESCE(last_used_at, '') ASC, id ASC"
                ).fetchall()

                if not candidates:
                    break

                joke_ids = [int(r["id"]) for r in candidates]
                random.shuffle(joke_ids)
                selected = next((jid for jid in joke_ids if jid not in used_ids), joke_ids[0])
                used_ids.add(selected)

                conn.execute(
                    "INSERT INTO joke_rotation (day_key, joke_id, assigned_at) VALUES (?, ?, ?)",
                    (day_key, selected, now),
                )
                assigned += 1

            conn.commit()

        return assigned

    def get_joke_for_day(self, day_key: str) -> str:
        self.ensure_inventory(min_count=ROTATION_DAYS)
        self.build_rotation(days=ROTATION_DAYS)

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT r.joke_id, j.body
                FROM joke_rotation r
                JOIN jokes j ON j.id = r.joke_id
                WHERE r.day_key = ?
                """,
                (day_key,),
            ).fetchone()

            if row:
                now = dt.datetime.now(dt.timezone.utc).isoformat()
                conn.execute(
                    "UPDATE jokes SET use_count = use_count + 1, last_used_at = ? WHERE id = ?",
                    (now, int(row["joke_id"])),
                )
                conn.execute(
                    "UPDATE joke_rotation SET sent_at = COALESCE(sent_at, ?) WHERE day_key = ?",
                    (now, day_key),
                )
                conn.commit()
                return str(row["body"])

        local = self._load_local_jokes()
        if local:
            return sanitize_text(random.choice(local))
        return sanitize_text("Weedcoin OG says: keep it green, keep it chill.")

    def get_today_joke(self, now_utc: dt.datetime | None = None) -> str:
        now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
        return self.get_joke_for_day(now_utc.date().isoformat())


_STORE: JokeRotationStore | None = None
_STORE_LOCK = threading.Lock()


def get_store() -> JokeRotationStore:
    global _STORE
    if _STORE is None:
        with _STORE_LOCK:
            if _STORE is None:
                _STORE = JokeRotationStore()
    return _STORE


def get_rotating_joke(now_utc: dt.datetime | None = None) -> str:
    return get_store().get_today_joke(now_utc=now_utc)
