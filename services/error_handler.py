import logging
from telegram.error import NetworkError, TelegramError

logger = logging.getLogger(__name__)


async def on_error(update, context):
    """Handle errors in bot operations with structured logging."""
    # chat_id is None when there's no update (e.g. scheduler errors, network blips)
    chat_id = update.effective_chat.id if update and update.effective_chat else None
    user_id = update.effective_user.id if update and update.effective_user else "unknown"

    error = context.error

    # Handle network errors gracefully (common during polling)
    if isinstance(error, NetworkError):
        logger.warning(
            "Network error during polling | chat=%s user=%s",
            chat_id, user_id,
            exc_info=error,
        )
        return

    # Handle Telegram API errors
    if isinstance(error, TelegramError):
        logger.warning(
            "Telegram API error | chat=%s user=%s | %s",
            chat_id, user_id, error.message,
            exc_info=error,
        )
        if chat_id is not None:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Telegram API temporarily unavailable. Please try again in a moment.",
                )
            except Exception as notify_err:
                logger.warning("Failed to notify user of API error: %s", notify_err)
        return

    # Log all other exceptions
    logger.exception(
        "Unhandled error in bot | chat=%s user=%s",
        chat_id, user_id,
        exc_info=error,
    )

    # Only notify if we have a real chat to send to
    if chat_id is not None:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="An unexpected error occurred. Our team has been notified.",
            )
        except Exception as notify_err:
            logger.warning("Failed to notify user of error: %s", notify_err)
