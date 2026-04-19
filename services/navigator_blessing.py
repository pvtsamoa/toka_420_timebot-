"""
Navigator's Blessing — Rotating Faasamoan-inspired wisdom for crypto navigation
"""
import logging
import random

logger = logging.getLogger(__name__)

# Faasamoan culture + cryptocurrency navigation wisdom (plain text — no Markdown asterisks)
BLESSINGS = [
    "🌊 Fa'a Samoa — Navigate the markets with ancestral wisdom. May your holdings drift gently like outrigger canoes on calm seas.",
    "🌴 Lelei le ala — The path is good. Trust in steady accumulation, fear not the volatile tides of speculation.",
    "⛵ Fautasi blessing — As the great war canoe cuts through waves, so too shall your Weedcoin journey be swift and purposeful.",
    "🌺 Talofa — A greeting to the markets. May your trades be blessed with wisdom and your bags with abundance.",
    "🔮 The Navigator's Star — Like our ancestors read the stars, read the charts. Patience rewards the disciplined trader.",
    "🌊 Moana blessing — The ocean connects all islands. Decentralization connects all holders. You are not alone.",
    "💚 Faleula — The sacred covenant. Honor your vision, protect your seeds, tend your garden with care.",
    "🧭 Vaai le ala — Look to the path ahead. DYOR, hodl strong, and let time compound your vision.",
    "🌿 Gafatia — Root yourself in fundamentals. Weeds grow where others see only dirt — we see abundance.",
    "⚡ Matagi blessing — May the winds of fortune fill your sails. Ride the cycles, fear not the seasons.",
]


def get_blessing() -> str:
    """Return a random Navigator's Blessing."""
    blessing = random.choice(BLESSINGS)
    logger.debug("Navigator's Blessing selected: %s...", blessing[:30])
    return blessing
