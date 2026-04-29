import os
import logging
from services.security import validate_env_vars

logger = logging.getLogger(__name__)

def validate_config():
    """Validate all required environment variables at startup."""
    required_vars = {
        "TELEGRAM_BOT_TOKEN": "Telegram bot token from BotFather",
        "TELEGRAM_GLOBAL_CHAT_ID": "Telegram group chat ID where rituals will be posted",
    }
    
    optional_vars = {
        "DEFAULT_TOKEN": "Default crypto token (default: weedcoin)",
        "TZ": "Timezone (default: America/Los_Angeles)",
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        # Check for placeholder values
        if not value or value.startswith("YOUR_"):
            missing.append(f"  {var}: {description}")
        
        # Security: warn if value looks unusual
        if value and len(value) < 5:
            missing.append(f"  {var}: Value too short (likely placeholder)")
    
    if missing:
        error_msg = "ERROR: Missing or invalid environment variables:\n" + "\n".join(missing)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Log optional vars status (without exposing values)
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"OK {var} configured")
        else:
            logger.info(f"INFO {var} not set (will use default)")
    
    # Validate that secrets aren't exposed
    warnings = validate_env_vars()
    if warnings:
        logger.warning("WARNING Configuration issues: %s", ", ".join(warnings))
    
    logger.info("OK All required configuration validated")
