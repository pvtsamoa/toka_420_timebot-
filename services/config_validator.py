import os
import logging
import pytz

logger = logging.getLogger(__name__)

def validate_config():
    """Validate all required environment variables at startup."""
    required_vars = {
        "TELEGRAM_BOT_TOKEN": "Telegram bot token from BotFather",
        "TELEGRAM_GLOBAL_CHAT_ID": "Telegram group chat ID where rituals will be posted",
    }
    
    optional_vars = {
        "TELEGRAM_SCOPE": "all|apac|emea|amer",
        "DEFAULT_TOKEN": "Default crypto token (default: weedcoin)",
        "WEEDCOIN_TOKEN": "Weedcoin symbol (default: Weedcoin)",
        "TZ": "Timezone (default: America/Los_Angeles)",
    }
    allowed_scopes = {"all", "apac", "emea", "amer"}
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  {var}: {description}")
    
    if missing:
        error_msg = "Missing required environment variables:\n" + "\n".join(missing)
        logger.error(error_msg)
        raise ValueError(error_msg)

    scope = (os.getenv("TELEGRAM_SCOPE") or "all").lower()
    if scope not in allowed_scopes:
        raise ValueError(
            f"Invalid TELEGRAM_SCOPE: {scope}. Expected one of {sorted(allowed_scopes)}"
        )

    tz_name = os.getenv("TZ", "America/Los_Angeles")
    try:
        pytz.timezone(tz_name)
    except Exception as e:
        raise ValueError(f"Invalid TZ value: {tz_name}") from e
    
    # Log optional vars status
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"{var} configured")
        else:
            logger.info(f"{var} not set (will use default)")
    
    logger.info("All required configuration validated")
