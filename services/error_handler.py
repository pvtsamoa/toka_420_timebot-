import logging
from telegram.error import NetworkError, TelegramError

logger = logging.getLogger(__name__)

async def on_error(update, context):
    """Handle errors in bot operations with structured logging."""
    # Extract context information
    chat_id = update.effective_chat.id if update and update.effective_chat else "unknown"
    user_id = update.effective_user.id if update and update.effective_user else "unknown"
    
    error = context.error
    
    # Handle network errors gracefully (common during polling)
    if isinstance(error, NetworkError):
        logger.warning(
            f"Network error during polling | chat={chat_id} user={user_id}",
            exc_info=error
        )
        return
    
    # Handle Telegram API errors
    if isinstance(error, TelegramError):
        logger.warning(
            f"Telegram API error | chat={chat_id} user={user_id} | {error.message}",
            exc_info=error
        )
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="âš ï¸ Telegram API temporarily unavailable. Please try again in a moment."
            )
        except Exception as notify_err:
            logger.exception(f"Failed to notify user of API error: {notify_err}")
        return
    
    # Log all other exceptions
    logger.exception(
        f"Unhandled error in bot | chat={chat_id} user={user_id}",
        exc_info=error
    )
    
    # Try to notify user
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="ðŸ’¥ An unexpected error occurred. Our team has been notified."
        )
    except Exception as notify_err:
        logger.exception(f"Failed to notify user of error: {notify_err}")
