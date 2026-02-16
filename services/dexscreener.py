import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

DEX_URL_TOKEN = "https://api.dexscreener.com/latest/dex/tokens/{id}"
DEX_URL_SEARCH = "https://api.dexscreener.com/latest/dex/search?q={q}"
TIMEOUT = 10
_cache = {"key": None, "data": None, "ts": 0, "ttl": 60}

def _http_json(url: str):
    """Fetch and parse JSON from URL."""
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        r.raise_for_status()
        return r.json()
    except requests.Timeout:
        logger.warning(f"Request timeout: {url}")
        raise
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        raise
    except ValueError as e:
        logger.warning(f"Invalid JSON from {url}: {e}")
        raise

def _pick_pair(payload):
    """Select the pair with highest 24h volume."""
    pairs = (payload or {}).get("pairs") or []
    if not pairs:
        logger.debug("No pairs in payload")
        return None
    try:
        return sorted(
            pairs,
            key=lambda p: float(p.get("volume", {}).get("h24") or 0),
            reverse=True
        )[0]
    except Exception as e:
        logger.warning(f"Error selecting pair: {e}")
        return None

def _format_anchor(pair):
    """Format pair data into user-friendly anchor message."""
    try:
        price = pair.get("priceUsd") or pair.get("priceNative") or "?"
        change = pair.get("priceChange", {}).get("h24")
        vol24 = pair.get("volume", {}).get("h24")
        
        # Format price
        try:
            price = f"${float(price):,.6f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            price = "N/A"
        
        # Format change
        try:
            change_txt = f"{float(change):+.2f}%" if change else "Â±0.00%"
        except (ValueError, TypeError):
            change_txt = "Â±0.00%"
        
        # Format volume
        try:
            vol24_txt = f"${float(vol24):,.0f}" if vol24 else "$0"
        except (ValueError, TypeError):
            vol24_txt = "$0"
        
        symbol = pair.get("baseToken", {}).get("symbol") or "TOKEN"
        
        return {
            "symbol": symbol,
            "price": price,
            "change24": change_txt,
            "vol24": vol24_txt,
            "chain": pair.get("chainId") or pair.get("chain") or "",
            "dex": pair.get("dexId") or "",
            "pair": pair.get("pairAddress") or ""
        }
    except Exception as e:
        logger.exception(f"Error formatting anchor: {e}")
        return None

def get_anchor(token_id: str):
    """Get formatted anchor data for a token, with caching."""
    now = time.time()
    
    # Check cache
    if _cache["key"] == token_id and now - _cache["ts"] < _cache["ttl"]:
        logger.debug(f"Cache hit for {token_id}")
        return _cache["data"]
    
    try:
        logger.debug(f"Fetching data for {token_id}...")
        
        # Try token endpoint first
        j = _http_json(DEX_URL_TOKEN.format(id=token_id))
        pair = _pick_pair(j)
        
        # Fallback to search endpoint
        if not pair:
            logger.debug(f"No pair found by ID, searching: {token_id}")
            j = _http_json(DEX_URL_SEARCH.format(q=token_id))
            pair = _pick_pair(j)
        
        if not pair:
            logger.warning(f"No trading pair found for {token_id}")
            return None
        
        # Format and cache
        data = _format_anchor(pair)
        if data:
            _cache.update({"key": token_id, "data": data, "ts": now})
            logger.debug(f"âœ… Got anchor for {token_id}: {data['symbol']} {data['price']}")
        
        return data
        
    except requests.Timeout:
        logger.warning(f"DexScreener timeout for {token_id}")
        return None
    except requests.RequestException as e:
        logger.warning(f"DexScreener error for {token_id}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error getting anchor for {token_id}: {e}")
        return None
