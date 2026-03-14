import datetime as dt
import hashlib
import json
import logging
import os
import random
import re
import sqlite3
from html import unescape
from typing import Iterable
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "jokes.db")
DEFAULT_JOKES_PATH = os.path.join(PROJECT_ROOT, "media", "jokes.json")
ROTATION_DAYS = 15
DEFAULT_REDDIT_FEEDS = [
    "https://www.reddit.com/r/dankmemes/new.json?limit=50",
    "https://www.reddit.com/r/Jokes/new.json?limit=50",
    "https://www.reddit.com/r/funny/new.json?limit=50",
]
DEFAULT_X_ACCOUNT_URL = "https://x.com/weedcoinOG"
DEFAULT_X_COMMUNITY_URL = "https://x.com/i/communities/1907131002478285013"


class JokeRotationStore:
    """Persistent joke rotation store with external source chain and local fallback."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, jokes_path: str = DEFAULT_JOKES_PATH):
        self.db_path = db_path
        self.jokes_path = jokes_path
        self.blacklist_terms = self._load_blacklist_terms()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.ensure_schema()

    @staticmethod
    def _load_blacklist_terms() -> list[str]:
        raw = os.getenv("JOKE_BLACKLIST_TERMS", "marijuana")
        return [x.strip().lower() for x in raw.split(",") if x.strip()]

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
        parts = (text or "").strip().split()
        return " ".join(parts)

    @staticmethod
    def _fingerprint(text: str) -> str:
        normalized = JokeRotationStore._normalize_text(text).lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _is_candidate_safe(self, text: str) -> bool:
        t = (text or "").lower()
        if len(t) < 8 or len(t) > 400:
            return False
        blocked = [
            "seed phrase",
            "wallet connect",
            "walletconnect",
            "send me your",
            "airdrop link",
            "guaranteed profit",
        ] + self.blacklist_terms
        return not any(token in t for token in blocked)

    def _insert_candidates(self, candidates: Iterable[str], source: str) -> int:
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        inserted = 0

        with self._connect() as conn:
            for raw in candidates:
                body = self._normalize_text(raw)
                if not body or not self._is_candidate_safe(body):
                    continue
                fp = self._fingerprint(body)
                try:
                    conn.execute(
                        """
                        INSERT INTO jokes (body, source, fingerprint, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
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
            logger.warning("Could not load local jokes fallback: %s", e)
        return []

    @staticmethod
    def _extract_from_weedcoin_html(html_text: str) -> list[str]:
        """Extract meme-like candidate lines from Weedcoin site HTML pages."""
        if not html_text:
            return []

        candidates = []

        # Pull anchor text for meme-joint links and convert titles into playful lines.
        for href, label in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_text, flags=re.I | re.S):
            clean_label = re.sub(r"<[^>]+>", "", label)
            clean_label = unescape(" ".join(clean_label.split())).strip()
            href_l = (href or "").lower()

            if not clean_label:
                continue
            if "/meme-joint/" in href_l:
                candidates.append(f"Meme Joint drop: {clean_label}.")

        # Pull headings that often represent meme-page slogans.
        for heading in re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html_text, flags=re.I | re.S):
            clean = re.sub(r"<[^>]+>", "", heading)
            clean = unescape(" ".join(clean.split())).strip()
            if not clean:
                continue
            low = clean.lower()
            if any(k in low for k in ("meme", "weedcoin", "high on humor")):
                candidates.append(clean)

        return candidates

    @staticmethod
    def _extract_from_x_account_html(html_text: str) -> list[str]:
        """Best-effort extraction of post-like text from public X account HTML."""
        if not html_text:
            return []

        candidates = []

        # Some rendered payloads embed tweet text in JSON blobs.
        for raw in re.findall(r'"full_text"\s*:\s*"(.*?)"', html_text):
            txt = raw.encode("utf-8").decode("unicode_escape", errors="ignore")
            txt = unescape(txt).replace("\\n", " ").replace("\\/", "/")
            txt = re.sub(r"https?://\S+", "", txt)
            txt = " ".join(txt.split()).strip()
            if txt:
                candidates.append(txt)

        # Fallback pattern for snippets rendered with tweetText markers.
        for raw in re.findall(r'data-testid="tweetText"[^>]*>(.*?)</', html_text, flags=re.I | re.S):
            txt = re.sub(r"<[^>]+>", "", raw)
            txt = unescape(" ".join(txt.split())).strip()
            if txt:
                candidates.append(txt)

        return candidates

    def _fetch_external_source(self, url: str, timeout: float = 8.0) -> list[str]:
        if not url:
            return []

        # X community pages are generally auth-gated; keep source optional and non-blocking.
        if "x.com/i/communities/" in url.lower():
            logger.info("X community URL requires authenticated scraping; skipping direct fetch: %s", url)
            return []

        try:
            res = requests.get(url, timeout=timeout, headers={"User-Agent": "Toka420Bot/1.0"})
            res.raise_for_status()

            host = (urlparse(url).hostname or "").lower()
            text_body = res.text or ""

            content_type = (res.headers.get("Content-Type") or "").lower()
            if "application/json" in content_type:
                payload = res.json()
                # Reddit JSON: data.children[].data.title/selftext
                if "reddit.com" in host and isinstance(payload, dict):
                    out = []
                    children = (((payload.get("data") or {}).get("children")) or [])
                    for child in children:
                        data = child.get("data") if isinstance(child, dict) else None
                        if not isinstance(data, dict):
                            continue
                        title = (data.get("title") or "").strip()
                        selftext = (data.get("selftext") or "").strip()
                        if title and selftext:
                            out.append(f"{title} - {selftext}")
                        elif title:
                            out.append(title)
                    return out

                if isinstance(payload, list):
                    return [str(item) for item in payload if isinstance(item, str)]
                if isinstance(payload, dict):
                    for key in ("items", "jokes", "posts", "data"):
                        val = payload.get(key)
                        if isinstance(val, list):
                            out = []
                            for item in val:
                                if isinstance(item, str):
                                    out.append(item)
                                elif isinstance(item, dict):
                                    txt = item.get("text") or item.get("title") or item.get("body")
                                    if isinstance(txt, str):
                                        out.append(txt)
                            return out
                return []

            if "weedcoinog.com" in host:
                extracted = self._extract_from_weedcoin_html(text_body)
                if extracted:
                    return extracted

            if host.endswith("x.com") and "/i/communities/" not in url.lower():
                extracted = self._extract_from_x_account_html(text_body)
                if extracted:
                    return extracted

            lines = []
            for line in text_body.splitlines():
                line = line.strip()
                if line:
                    lines.append(line)
            return lines
        except Exception as e:
            logger.info("External joke source unavailable (%s): %s", url, e)
            return []

    def refresh_inventory(self) -> int:
        """Refresh joke inventory from source chain and local fallback."""
        inserted = 0

        site_url = os.getenv("WEEDCOINOG_SITE_JOKES_URL", "").strip()
        x_url = os.getenv("WEEDCOINOG_X_JOKES_URL", "").strip()
        x_account_url = os.getenv("WEEDCOINOG_X_ACCOUNT_URL", DEFAULT_X_ACCOUNT_URL).strip()
        x_community_url = os.getenv("WEEDCOINOG_X_COMMUNITY_URL", DEFAULT_X_COMMUNITY_URL).strip()
        reddit_urls = [
            u.strip()
            for u in os.getenv("JOKE_REDDIT_FEEDS", "").split(",")
            if u.strip()
        ]
        if len(reddit_urls) == 1 and reddit_urls[0].lower() in {"off", "none", "disabled"}:
            reddit_urls = []
        elif not reddit_urls:
            reddit_urls = DEFAULT_REDDIT_FEEDS

        if site_url:
            inserted += self._insert_candidates(self._fetch_external_source(site_url), "weedcoinog_site")
        if x_url:
            inserted += self._insert_candidates(self._fetch_external_source(x_url), "weedcoinog_x")

        if x_account_url.lower() in {"off", "none", "disabled"}:
            x_account_url = ""
        if x_community_url.lower() in {"off", "none", "disabled"}:
            x_community_url = ""

        if x_account_url:
            inserted += self._insert_candidates(self._fetch_external_source(x_account_url), "x_account")

        if x_community_url:
            inserted += self._insert_candidates(self._fetch_external_source(x_community_url), "x_community")

        for url in reddit_urls:
            inserted += self._insert_candidates(self._fetch_external_source(url), "reddit")

        # Always keep local file as resilient fallback seed.
        inserted += self._insert_candidates(self._load_local_jokes(), "local_fallback")
        return inserted

    def _count_active(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM jokes WHERE active = 1").fetchone()
            return int(row["c"] if row else 0)

    def ensure_inventory(self, min_count: int = 15) -> None:
        if self._count_active() >= min_count:
            return
        self.refresh_inventory()

    def build_rotation(self, days: int = ROTATION_DAYS, start_date: dt.date | None = None) -> int:
        """Assign jokes for missing day keys over a rolling window."""
        self.ensure_inventory(min_count=days)
        start_date = start_date or dt.datetime.now(dt.timezone.utc).date()
        assigned = 0

        with self._connect() as conn:
            # Preload upcoming assigned joke ids to reduce repetition.
            existing_rows = conn.execute(
                """
                SELECT day_key, joke_id
                FROM joke_rotation
                WHERE day_key >= ? AND day_key <= ?
                """,
                (
                    start_date.isoformat(),
                    (start_date + dt.timedelta(days=days - 1)).isoformat(),
                ),
            ).fetchall()

            used_ids = {int(r["joke_id"]) for r in existing_rows}
            now = dt.datetime.now(dt.timezone.utc).isoformat()

            for offset in range(days):
                day_key = (start_date + dt.timedelta(days=offset)).isoformat()
                exists = conn.execute(
                    "SELECT joke_id FROM joke_rotation WHERE day_key = ?",
                    (day_key,),
                ).fetchone()
                if exists:
                    continue

                candidates = conn.execute(
                    """
                    SELECT id
                    FROM jokes
                    WHERE active = 1
                    ORDER BY use_count ASC, COALESCE(last_used_at, '') ASC, id ASC
                    """
                ).fetchall()

                if not candidates:
                    break

                joke_ids = [int(r["id"]) for r in candidates]
                random.shuffle(joke_ids)

                selected = next((jid for jid in joke_ids if jid not in used_ids), joke_ids[0])
                used_ids.add(selected)

                conn.execute(
                    """
                    INSERT INTO joke_rotation (day_key, joke_id, assigned_at)
                    VALUES (?, ?, ?)
                    """,
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
                conn.execute("UPDATE jokes SET use_count = use_count + 1, last_used_at = ? WHERE id = ?", (now, int(row["joke_id"])))
                conn.execute("UPDATE joke_rotation SET sent_at = COALESCE(sent_at, ?) WHERE day_key = ?", (now, day_key))
                conn.commit()
                return str(row["body"])

        local = self._load_local_jokes()
        if local:
            return random.choice(local)
        return "Weedcoin OG says: keep it green, keep it chill."

    def get_today_joke(self, now_utc: dt.datetime | None = None) -> str:
        now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
        return self.get_joke_for_day(now_utc.date().isoformat())


_STORE: JokeRotationStore | None = None


def get_store() -> JokeRotationStore:
    global _STORE
    if _STORE is None:
        _STORE = JokeRotationStore()
    return _STORE


def get_rotating_joke(now_utc: dt.datetime | None = None) -> str:
    return get_store().get_today_joke(now_utc=now_utc)
