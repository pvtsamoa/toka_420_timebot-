import logging
import os
from types import SimpleNamespace

from telegram import Update
from telegram.ext import ContextTypes

from services.ritual_time import ritual_call

logger = logging.getLogger(__name__)


def _build_payload_for_now(app) -> dict:
    tz_name = os.getenv("TZ", "America/Los_Angeles")
    all_hubs = app.bot_data.get("all_hubs", []) if app else []
    hubs_in_tz = [hub for hub in all_hubs if hub.get("tz") == tz_name]

    if not hubs_in_tz:
        hubs_in_tz = [
            {
                "hub": "manual",
                "tier": "global",
                "tz": tz_name,
                "display": tz_name,
            }
        ]

    return {"tz": tz_name, "hubs": hubs_in_tz}


async def blessnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual trigger: send the current Green Hours blessing immediately."""
    message = update.effective_message
    chat = update.effective_chat

    if not message or not chat:
        return

    target_chat_id = os.getenv("TELEGRAM_GLOBAL_CHAT_ID", "").strip()
    if target_chat_id and str(chat.id) != target_chat_id:
        await message.reply_text("Manual blessing is only enabled in the configured global ritual chat.")
        return

    payload = _build_payload_for_now(context.application)
    shim_context = SimpleNamespace(
        job=SimpleNamespace(data=payload),
        application=context.application,
        bot=context.bot,
    )

    try:
        await ritual_call(shim_context)
        await message.reply_text("Current Green Hours blessing pushed now.")
        logger.info("Manual blessing triggered by chat=%s", chat.id)
    except Exception as exc:
        logger.exception("Manual blessing trigger failed: %s", exc)
        await message.reply_text("Manual blessing trigger failed. Check logs and try again.")
