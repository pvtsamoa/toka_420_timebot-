import os
import time
import logging
from typing import Any, Dict, List, Optional

import requests

from services.dexscreener import get_anchor

logger = logging.getLogger(__name__)

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
REQUEST_TIMEOUT = 10
CACHE_TTL = 180

_cache: Dict[str, Any] = {
    "ts": 0,
    "snapshot": None,
}


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_price(price: Optional[float]) -> str:
    if price is None:
        return "n/a"
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:,.6f}".rstrip("0").rstrip(".")


def _fmt_pct(change: Optional[float]) -> str:
    if change is None:
        return "n/a"
    return f"{change:+.2f}%"


def _fetch_markets() -> List[Dict[str, Any]]:
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 80,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    resp = requests.get(
        COINGECKO_MARKETS_URL,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload if isinstance(payload, list) else []


def get_market_snapshot() -> Dict[str, Any]:
    now = time.time()
    if _cache.get("snapshot") and now - _cache.get("ts", 0) < CACHE_TTL:
        return _cache["snapshot"]

    weedcoin_id = os.getenv("DEFAULT_TOKEN", "weedcoin").strip().lower()
    weedcoin_anchor = get_anchor(weedcoin_id)
    weedcoin_line = (
        f"{weedcoin_anchor.get('symbol', 'WEEDCOIN').upper()}: "
        f"{weedcoin_anchor.get('price', 'n/a')} | "
        f"24h {weedcoin_anchor.get('change24', 'n/a')} | "
        f"vol {weedcoin_anchor.get('vol24', 'n/a')}"
        if weedcoin_anchor
        else "WEEDCOIN: n/a"
    )

    snapshot = {
        "weedcoin": weedcoin_line,
        "top5": [],
    }

    try:
        markets = _fetch_markets()
        top5 = []
        for row in markets[:5]:
            symbol = (row.get("symbol") or "?").upper()
            pct = _fmt_pct(_safe_float(row.get("price_change_percentage_24h_in_currency")))
            price = _fmt_price(_safe_float(row.get("current_price")))
            top5.append(f"{symbol} {pct} @ {price}")

        snapshot["top5"] = top5
    except Exception as e:
        logger.warning("Market snapshot fallback mode: %s", e)

    _cache["ts"] = now
    _cache["snapshot"] = snapshot
    return snapshot


def format_market_snapshot_lines() -> List[str]:
    snap = get_market_snapshot()
    lines = [f"Weedcoin OG: {snap.get('weedcoin', 'n/a')}"]
    top5 = snap.get("top5") or []
    if top5:
        for idx, line in enumerate(top5, start=1):
            lines.append(f"Top {idx}: {line}")
    else:
        lines.append("Top 5: n/a")
    return lines