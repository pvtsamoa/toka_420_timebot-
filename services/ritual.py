import os
import logging
from typing import Any, Optional

from services.content_policy import sanitize_text
from services.dexscreener import get_anchor
from services.joke_rotation import get_rotating_joke

logger = logging.getLogger(__name__)


def _weedcoin_line() -> str:
    """
    Fetch Weedcoin OG price from DexScreener, preferring the Solana pair.

    WEEDCOIN_TOKEN env  — contract address or search term (default: weedcoin)
    WEEDCOIN_CHAIN env  — chain to prefer (default: solana)

    The display label is always $WEEDCOIN regardless of what DexScreener
    returns as the symbol, because the brand is $WEEDCOIN not $WEED.
    """
    token_id = os.getenv("WEEDCOIN_TOKEN", "weedcoin").strip()
    chain    = os.getenv("WEEDCOIN_CHAIN", "solana").strip()
    try:
        data = get_anchor(token_id, prefer_chain=chain)
        if not data:
            return "$WEEDCOIN: price n/a"
        change24 = data.get("change24", "+/-0.00%")
        price    = data.get("price", "n/a")
        vol24    = data.get("vol24", "$0")
        return f"$WEEDCOIN: {change24} | {price} | 24h vol {vol24}"
    except Exception as e:
        logger.exception("Error fetching Weedcoin price: %s", e)
        return "$WEEDCOIN: price n/a"


def _secondary_line() -> tuple[str, str]:
    """
    Fetch secondary token price from DexScreener.

    SECONDARY_TOKEN env — any token (default: ethereum)

    Returns (label, price_line) so the caller can build the section header
    using the real symbol from DexScreener (e.g. BTC, SOL, BONK).
    """
    token_id = os.getenv("SECONDARY_TOKEN", "ethereum").strip()
    try:
        data = get_anchor(token_id)
        if not data:
            return token_id.upper(), f"{token_id.upper()}: price n/a"
        symbol   = data.get("symbol") or token_id.upper()
        change24 = data.get("change24", "+/-0.00%")
        price    = data.get("price", "n/a")
        vol24    = data.get("vol24", "$0")
        return f"${symbol}", f"${symbol}: {change24} | {price} | 24h vol {vol24}"
    except Exception as e:
        logger.exception("Error fetching secondary token price: %s", e)
        label = token_id.upper()
        return f"${label}", f"${label}: price n/a"


# kiss_anchor kept for blessnow and any callers that pass a token directly
def kiss_anchor(token_id: Optional[str]) -> str:
    token_id = (token_id or "weedcoin").strip()
    try:
        data = get_anchor(token_id)
        if not data:
            return f"{token_id.upper()}: price n/a"
        symbol   = data.get("symbol", token_id.upper())
        change24 = data.get("change24", "+/-0.00%")
        price    = data.get("price", "n/a")
        vol24    = data.get("vol24", "$0")
        return f"{symbol}: {change24} | {price} | 24h vol {vol24}"
    except Exception as e:
        logger.exception("Error getting anchor for %s: %s", token_id, e)
        return f"{token_id.upper()}: price n/a"


def build_ritual_text(
    hub: Any = None,
    *,
    city: Optional[str] = None,
    hub_name: Optional[str] = None,
    tier: Optional[str] = None,
) -> str:
    """
    Build the 4:20 Green Hour ritual message.

    Sections:
      1. Green Hour header — location
      2. Navigator's Blessing
      3. $WEEDCOIN price   — Weedcoin OG on Solana, global cannabis culture coin
      4. Secondary token   — any token set via SECONDARY_TOKEN env
      5. Joke / meme send-off
    """
    try:
        from services.navigator_blessing import get_blessing

        if isinstance(hub, dict):
            display_place = city or hub.get("display") or hub.get("hub") or "your timezone"
        else:
            display_place = city or hub_name or "your timezone"

        blessing                    = get_blessing()
        weedcoin_price_line         = _weedcoin_line()
        secondary_label, secondary_price_line = _secondary_line()
        joke                        = sanitize_text(get_rotating_joke())

        lines = [
            f"🌿 4:20 — {display_place}",
            "",
            blessing,
            "",
            "💰 $WEEDCOIN — Weedcoin OG | Solana | Cannabis Culture",
            weedcoin_price_line,
            "",
            f"📈 {secondary_label}",
            secondary_price_line,
            "",
            joke,
        ]

        return "\n".join(lines)

    except Exception as e:
        logger.exception("Error building ritual text: %s", e)
        place = city or hub_name or "your timezone"
        return f"🌿 4:20 — {place}\nError generating ritual. Please retry."
