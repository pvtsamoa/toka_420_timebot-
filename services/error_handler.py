import logging
from telegram.error import NetworkError, TelegramError
from services.security import sanitize_string

logger = logging.getLogger(__name__)

async def on_error(update, context):
    """Handle errors in bot operations with structured logging."""
    chat_id = update.effective_chat.id if update and update.effective_chat else "unknown"
    user_id = update.effective_user.id if update and update.effective_user else "unknown"

    error = context.error

    if isinstance(error, NetworkError):
        logger.warning(
            "Network error during polling | chat=%s user=%s",
            chat_id, user_id,
            exc_info=error
        )
        return

    if isinstance(error, TelegramError):
        # Sanitize error message in case it contains sensitive data
        sanitized_msg = sanitize_string(str(error.message)) if hasattr(error, 'message') else sanitize_string(str(error))
        logger.warning(
            "Telegram API error | chat=%s user=%s | %s",
            chat_id, user_id, sanitized_msg,
            exc_info=error
        )
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Telegram API temporarily unavailable. Please try again in a moment."
            )
        except Exception as notify_err:
            logger.exception("Failed to notify user of API error: %s", notify_err)
        return

    logger.exception(
        "Unhandled error in bot | chat=%s user=%s",
        chat_id, user_id,
        exc_info=error
    )

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="An unexpected error occurred. Our team has been notified."
        )
    except Exception as notify_err:
        logger.exception("Failed to notify user of error: %s", notify_err)
