import os
import random
import json
import logging
from typing import Any, Dict, List, Optional

from services.dexscreener import get_anchor

logger = logging.getLogger(__name__)

# Use the official token name consistently
DEFAULT_TOKEN = os.getenv("DEFAULT_TOKEN", "weedcoin")


def _pick(lst, default=None):
    """Safely pick a random item from a list."""
    if default is None:
        default = ""
    try:
        return random.choice(lst) if lst else default
    except Exception as e:
        logger.warning("Error picking from list: %s", e)
        return default


def _load_json(path: str):
    """Safely load JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug("Loaded JSON from %s", path)
            return data
    except FileNotFoundError:
        logger.warning("JSON file not found: %s", path)
        return []
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path, e)
        return []
    except Exception as e:
        logger.exception("Error loading JSON from %s: %s", path, e)
        return []


def _project_root() -> str:
    """
    Resolve repo root robustly.

    This file is in services/, so repo root is one level up from this file's directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_media_bank() -> Dict[str, List[Any]]:
    """Load all media files (quotes, safety tips, tokens)."""
    base = os.path.join(_project_root(), "media")
    try:
        media = {
            "quotes": _load_json(os.path.join(base, "cannabis_quotes.json")) or [],
            "safety": _load_json(os.path.join(base, "safety.json")) or [],
            "tokens": _load_json(os.path.join(base, "cannabis_tokens.json")) or [],
        }
        logger.debug(
            "Loaded media bank: %d quotes, %d safety tips, %d tokens",
            len(media["quotes"]),
            len(media["safety"]),
            len(media["tokens"]),
        )
        return media
    except Exception as e:
        logger.exception("Failed to load media bank: %s", e)
        return {"quotes": [], "safety": [], "tokens": []}


MEDIA = load_media_bank()


def kiss_anchor(token_id: Optional[str]):
    """Get formatted price anchor for a token."""
    token_id = (token_id or DEFAULT_TOKEN).strip()
    try:
        data = get_anchor(token_id)
        if not data:
            logger.debug("No price data for %s", token_id)
            return f"{token_id}: price n/a | vol n/a | 24h +/-0.00%"

        # Be defensive with keys
        symbol = data.get("symbol", token_id)
        change24 = data.get("change24", "24h +/-0.00%")
        price = data.get("price", "price n/a")
        vol24 = data.get("vol24", "vol n/a")

        return f"{symbol}: {change24} | {price} | 24h vol {vol24}"
    except Exception as e:
        logger.exception("Error getting anchor for %s: %s", token_id, e)
        return f"{token_id}: price n/a | vol n/a | 24h +/-0.00%"


def _normalize_hub_fields(hub: Any, hub_name: Optional[str], city: Optional[str], tier: Optional[str]):
    """
    Supports both old calling style (hub_name str) and new hub dict style.
    """
    if isinstance(hub, dict):
        tz = hub.get("tz")
        hub_id = hub.get("hub") or hub.get("name") or hub_name
        hub_tier = hub.get("tier") or tier
        hub_city = city
        return hub_id, hub_city, hub_tier, tz

    return hub_name, city, tier, None


def build_ritual_text(
    hub: Any = None,
    token_id: Optional[str] = None,
    *,
    hub_name: Optional[str] = None,
    city: Optional[str] = None,
    tier: Optional[str] = None,
):
    """
    Build the formatted ritual message.

    New usage (recommended):
      build_ritual_text(hub_dict, token_id=..., city=...)

    Backward-compatible usage:
      build_ritual_text(hub_name="America/New_York", token_id=...)
    """
    try:
        from services.navigator_blessing import get_blessing

        resolved_hub_name, resolved_city, resolved_tier, _tz = _normalize_hub_fields(
            hub, hub_name, city, tier
        )

        display_place = resolved_city or resolved_hub_name or "your timezone"
        display_tier = f" ({resolved_tier})" if resolved_tier else ""

        blessing = get_blessing()

        # Token objects in cannabis_tokens.json may vary.
        # Normalize to avoid showing $WEED (not $WEEDCOIN) accidentally.
        token_obj = _pick(MEDIA.get("tokens", []), {"symbol": "WEEDCOIN", "name": "Weedcoin"})
        token_symbol = (token_obj.get("symbol") or "WEEDCOIN").strip()
        token_name = (token_obj.get("name") or "Weedcoin").strip()

        # Prefer explicit token_id argument if provided
        anchor_token_id = (token_id or token_symbol or DEFAULT_TOKEN).lower()
        anchor = kiss_anchor(anchor_token_id)

        safety = _pick(MEDIA.get("safety", []), "DYOR | Use 2FA | Secure your keys")

        quote_obj = _pick(MEDIA.get("quotes", []), {})
        quote_text = ""
        if isinstance(quote_obj, dict) and quote_obj:
            q = (quote_obj.get("quote") or "").strip()
            src = (quote_obj.get("source") or "Cannabis Culture").strip()
            if q:
                quote_text = f"\"{q}\" - {src}"

        lines = [
            f"ðŸŒ¿â›µï¸ SPARK IT UP: 4:20 in {display_place}{display_tier}!",
            "",
            "âœ¨ Navigator's Blessing",
            blessing,
            "",
            f"ðŸ’° Featured Token: {token_name}",
            anchor,
            "",
            "ðŸ›¡ï¸ Cryptocurrency Safety",
            safety,
        ]

        if quote_text:
            lines += ["", "ðŸŽ¬ Cannabis Culture", quote_text]

        lines += ["", "Spark responsibly. Hold wise. ðŸŒ²"]

        return "\n".join(lines)

    except Exception as e:
        logger.exception("Error building ritual text for hub=%s: %s", hub_name or hub, e)
        place = city or hub_name or "your timezone"
        return f"ðŸŒ¿â›µï¸ SPARK IT UP: 4:20 in {place}!\nâš ï¸ Error generating ritual. Please retry."
