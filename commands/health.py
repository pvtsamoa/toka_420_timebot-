"""
/health command - quick liveness check
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check endpoint to verify bot is running."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Health check requested by user %s", user_id)

    msg = update.effective_message
    if msg:
        await msg.reply_text("Toka is healthy and running")
