import time
import threading
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEX_URL_TOKEN = "https://api.dexscreener.com/latest/dex/tokens/{id}"
DEX_URL_SEARCH = "https://api.dexscreener.com/latest/dex/search?q={q}"
TIMEOUT = 10

# Keyed cache: (token_id, prefer_chain) -> {"data": ..., "ts": float}
_cache: dict[tuple, dict] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 60


def _http_json(url: str):
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        r.raise_for_status()
        return r.json()
    except requests.Timeout:
        logger.warning("Request timeout: %s", url)
        raise
    except requests.RequestException as e:
        logger.warning("Request failed for %s: %s", url, e)
        raise
    except ValueError as e:
        logger.warning("Invalid JSON from %s: %s", url, e)
        raise


def _pick_pair(payload, prefer_chain: Optional[str] = None):
    """
    Select the best trading pair from a DexScreener response.

    If prefer_chain is set (e.g. "solana"), pairs on that chain are tried first.
    Falls back to highest-volume pair across all chains if none found on preferred chain.
    """
    pairs = (payload or {}).get("pairs") or []
    if not pairs:
        logger.debug("No pairs in payload")
        return None

    def _by_volume(p):
        try:
            return float(p.get("volume", {}).get("h24") or 0)
        except (TypeError, ValueError):
            return 0.0

    try:
        if prefer_chain:
            chain_pairs = [
                p for p in pairs
                if (p.get("chainId") or "").lower() == prefer_chain.lower()
            ]
            if chain_pairs:
                return sorted(chain_pairs, key=_by_volume, reverse=True)[0]
            logger.debug(
                "No pairs found on chain %r — falling back to highest-volume pair", prefer_chain
            )

        return sorted(pairs, key=_by_volume, reverse=True)[0]
    except Exception as e:
        logger.warning("Error selecting pair: %s", e)
        return None


def _format_anchor(pair):
    """Format a DexScreener pair dict into a flat display dict."""
    try:
        price  = pair.get("priceUsd") or pair.get("priceNative") or "?"
        change = pair.get("priceChange", {}).get("h24")
        vol24  = pair.get("volume", {}).get("h24")

        try:
            price = f"${float(price):,.6f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            price = "N/A"

        try:
            change_txt = f"{float(change):+.2f}%" if change else "+/-0.00%"
        except (ValueError, TypeError):
            change_txt = "+/-0.00%"

        try:
            vol24_txt = f"${float(vol24):,.0f}" if vol24 else "$0"
        except (ValueError, TypeError):
            vol24_txt = "$0"

        symbol = pair.get("baseToken", {}).get("symbol") or "TOKEN"

        return {
            "symbol":   symbol,
            "price":    price,
            "change24": change_txt,
            "vol24":    vol24_txt,
            "chain":    pair.get("chainId") or pair.get("chain") or "",
            "dex":      pair.get("dexId") or "",
            "pair":     pair.get("pairAddress") or "",
        }
    except Exception as e:
        logger.exception("Error formatting anchor: %s", e)
        return None


def get_anchor(token_id: str, prefer_chain: Optional[str] = None):
    """
    Return formatted price data for a token, with per-token caching.

    prefer_chain: IANA chain ID (e.g. "solana", "ethereum") — selects pairs on
    that chain before falling back to highest-volume across all chains.
    """
    cache_key = (token_id, prefer_chain)
    now = time.time()

    with _cache_lock:
        entry = _cache.get(cache_key)
        if entry and now - entry["ts"] < _CACHE_TTL:
            logger.debug("Cache hit for %s (chain=%s)", token_id, prefer_chain)
            return entry["data"]

    try:
        logger.debug("Fetching %s (prefer_chain=%s)", token_id, prefer_chain)

        j    = _http_json(DEX_URL_TOKEN.format(id=token_id))
        pair = _pick_pair(j, prefer_chain=prefer_chain)

        if not pair:
            logger.debug("No pair by ID for %s — trying search", token_id)
            j    = _http_json(DEX_URL_SEARCH.format(q=token_id))
            pair = _pick_pair(j, prefer_chain=prefer_chain)

        if not pair:
            logger.warning("No trading pair found for %s", token_id)
            return None

        data = _format_anchor(pair)
        if data:
            with _cache_lock:
                _cache[cache_key] = {"data": data, "ts": time.time()}
            logger.debug(
                "Anchor for %s: %s %s (chain=%s)",
                token_id, data["symbol"], data["price"], data["chain"],
            )

        return data

    except requests.Timeout:
        logger.warning("DexScreener timeout for %s", token_id)
        return None
    except requests.RequestException as e:
        logger.warning("DexScreener error for %s: %s", token_id, e)
        return None
    except Exception as e:
        logger.exception("Unexpected error getting anchor for %s: %s", token_id, e)
        return None
