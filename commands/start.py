"""
/start command — Welcome and command reference
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message for the lean bot experience."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Start command requested (user: %s)", user_id)

    message = """
🌿⛵️ **Toka 420 Pulse**

Somewhere on this planet, it's always 4:20.
This bot stays focused on three things:

1. Bless the 4:20 moment
2. Show live crypto momentum (Weedcoin OG first)
3. List relevant cannabis + crypto headlines

────────────────────────

**COMMANDS**

**/status**
4:20 tracker + blessing + market snapshot

**/news**
Fresh cannabis and crypto headlines

**/health**
Quick uptime check

────────────────────────

May your timing stay blessed and your charts stay clear.
"""

    if update.effective_message:
        await update.effective_message.reply_text(message, parse_mode="Markdown")
