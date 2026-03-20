import os
import logging
import pytz

logger = logging.getLogger(__name__)


def validate_config() -> None:
    """Validate required environment variables at startup. Raises ValueError on failure."""
    required = {
        "TELEGRAM_BOT_TOKEN":      "Telegram bot token from BotFather",
        "TELEGRAM_GLOBAL_CHAT_ID": "Telegram group chat ID where rituals are posted",
    }

    missing = [f"  {var}: {desc}" for var, desc in required.items() if not os.getenv(var)]
    if missing:
        msg = "Missing required environment variables:\n" + "\n".join(missing)
        logger.error(msg)
        raise ValueError(msg)

    # Validate TELEGRAM_GLOBAL_CHAT_ID is an integer or @username
    chat_id = os.getenv("TELEGRAM_GLOBAL_CHAT_ID", "").strip()
    if not chat_id.startswith("@"):
        try:
            int(chat_id)
        except ValueError:
            raise ValueError(
                f"TELEGRAM_GLOBAL_CHAT_ID must be an integer chat ID or @username, got: {chat_id!r}"
            )

    # Validate TZ
    tz_name = os.getenv("TZ", "America/Los_Angeles")
    try:
        pytz.timezone(tz_name)
    except Exception as e:
        raise ValueError(f"Invalid TZ value: {tz_name!r}") from e

    # Log token config
    for var, default in [
        ("WEEDCOIN_TOKEN",  "weedcoin"),
        ("WEEDCOIN_CHAIN",  "solana"),
        ("SECONDARY_TOKEN", "ethereum"),
    ]:
        logger.info("%s = %s", var, os.getenv(var, default))

    logger.info("Configuration validated")
