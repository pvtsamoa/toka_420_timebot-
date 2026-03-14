"""
/start command — Welcome and command reference
"""
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with full command reference."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Start command requested (user: %s)", user_id)

    message = (
        "<b>Toka 420 Time Bot</b> — Welcome, Navigator\n\n"
        "Your guide through cannabis culture and cryptocurrency.\n"
        "Every day, somewhere in the world, it is 4:20 — and Toka marks the moment.\n\n"
        "<b>COMMANDS</b>\n\n"
        "/status — Bot health, scheduler status, price anchor, next ritual\n"
        "/news — Rotating market news (crypto to finance)\n"
        "/token [symbol] — Token price lookup (default: weedcoin)\n"
        "/studies — Cannabis research and awareness resources\n"
        "/health — Quick bot health check\n\n"
        "<b>AUTOMATED RITUALS</b>\n\n"
        "Fires daily at 04:20 local time in every active timezone.\n"
        "One ritual per timezone, rolling across the globe 24/7.\n\n"
        "Each ritual includes:\n"
        "- Price anchor (Weedcoin and featured token)\n"
        "- Navigator's Blessing\n"
        "- Cryptocurrency safety reminder\n\n"
        "<b>TIPS</b>\n\n"
        "Use /token weedcoin to track price movement\n"
        "Use /status to confirm the next local 4:20\n\n"
        "May the Navigator's blessing guide your timing and your trades."
    )

    if update.effective_message:
        await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)
