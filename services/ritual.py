import os
import random
import json
import logging
from typing import Any, Dict, List
from services.market_snapshot import format_market_snapshot_lines
from services.headlines import get_latest_cannabis_crypto_headline

logger = logging.getLogger(__name__)

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
    """Load media files used by rituals."""
    base = os.path.join(_project_root(), "media")
    try:
        media = {
            "quotes": _load_json(os.path.join(base, "cannabis_quotes.json")) or [],
            "jokes": _load_json(os.path.join(base, "jokes.json")) or [],
        }
        logger.debug(
            "Loaded media bank: %d quotes, %d jokes",
            len(media["quotes"]),
            len(media["jokes"]),
        )
        return media
    except Exception as e:
        logger.exception("Failed to load media bank: %s", e)
        return {"quotes": [], "jokes": []}


MEDIA = load_media_bank()


def build_ritual_text(ritual_hubs: List[Dict[str, Any]]):
    """
    Build compact 3-hub ritual message with matai speech.

    Args:
        ritual_hubs: List of dicts with keys: hub, city, tier
                     Example: [{"hub": {...}, "city": "Paris", "tier": "major"}, ...]

    Returns:
        Formatted ritual message string
    """
    try:
        from services.navigator_blessing import get_blessing

        if not ritual_hubs:
            return "🌿⛵ 4:20 Navigational Briefing\n⚠️ No hubs available at this time."

        # Extract cities and tiers
        city_lines = []
        for rh in ritual_hubs:
            city = rh.get("city") or "Unknown"
            tier = rh.get("tier") or "growing"

            # Nautical metaphors for each tier
            if tier == "major":
                metaphor = "canoe catches strong trade winds"
            elif tier == "minor":
                metaphor = "paddlers read the steady currents"
            else:  # growing
                metaphor = "crew plants seeds in fertile waters"

            city_lines.append(f"{city} {metaphor}")

        # Build city prose (matai speech - flowing, not bullets)
        if len(city_lines) == 1:
            city_prose = f"{city_lines[0]}.\nOne vessel on the great ocean."
        elif len(city_lines) == 2:
            city_prose = f"{city_lines[0]},\n{city_lines[1]}.\nTwo vessels, one ocean, same stars."
        else:
            city_prose = f"{city_lines[0]},\n{city_lines[1]},\n{city_lines[2]}.\nThree vessels, one ocean, same stars."

        # Get Navigator's blessing
        blessing = get_blessing()

        market_lines = format_market_snapshot_lines()
        market_prose = "\n".join(f"• {line}" for line in market_lines)

        latest_headline = get_latest_cannabis_crypto_headline()

        # Cannabis advocate quote option
        quote_obj = _pick(MEDIA.get("quotes", []), {})
        quote_text = ""
        if isinstance(quote_obj, dict) and quote_obj:
            q = (quote_obj.get("quote") or "").strip()
            src = (quote_obj.get("source") or "Cannabis Culture").strip()
            if q:
                quote_text = f'"{q}" - {src}'

        if not quote_text:
            quote_text = '"When you smoke the herb, it reveals you to yourself." - Bob Marley'

        joke_text = _pick(MEDIA.get("jokes", []), "Why did the blunt cross the road? To get to the other high.")
        use_joke = bool(MEDIA.get("jokes")) and random.random() < 0.5
        closer_title = "😂 Session Ender: Stoner Joke" if use_joke else "🌟 Session Ender: Cannabis Advocate Quote"
        closer_text = joke_text if use_joke else quote_text

        # Build final message
        lines = [
            "🌿⛵ Toka's Call: 4:20 Navigational Briefing",
            "",
            "✨ Tautai's Va (Navigator's Sacred Space)",
            city_prose,
            "",
            blessing,
            "",
            "🌊 Crypto Current Snapshot",
            market_prose,
            "",
            "🗞 Latest Cannabis x Crypto Headline",
            latest_headline,
            "",
            closer_title,
            closer_text,
        ]

        return "\n".join(lines)

    except Exception as e:
        logger.exception("Error building ritual text: %s", e)
        return "🌿⛵ 4:20 Navigational Briefing\n⚠️ Error generating ritual. Please retry."
