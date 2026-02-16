import os
import logging

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
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  {var}: {description}")
    
    if missing:
        error_msg = "âŒ Missing required environment variables:\n" + "\n".join(missing)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Log optional vars status
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"{var} configured")
        else:
            logger.info(f"{var} not set (will use default)")
    
    logger.info("All required configuration validated")
