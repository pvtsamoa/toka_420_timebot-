"""
Security utilities for protecting sensitive data.

Prevents accidental exposure of secrets in logs and error messages.
"""
import os
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Patterns to detect sensitive values
SENSITIVE_PATTERNS = {
    'token': r'[0-9]+:[A-Za-z0-9_-]{35,}',  # Telegram bot token pattern
    'key': r'[A-Za-z0-9]{40,}',  # Generic API key pattern
    'password': r'(?i)(password|passwd|pwd)[\s]*[=:]\s*[^\s]+',
    'secret': r'(?i)(secret|api_key)[\s]*[=:]\s*[^\s]+',
}

REDACTED = "***REDACTED***"


def sanitize_string(value: str, redact_length: int = 8) -> str:
    """
    Sanitize a string that might contain secrets.
    
    Args:
        value: The string to sanitize
        redact_length: Number of characters to show before redacting
        
    Returns:
        Sanitized string with secrets masked
    """
    if not isinstance(value, str):
        return str(value)
    
    if len(value) < 10:
        return value
    
    # Check if it matches any sensitive patterns
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if re.search(pattern, value):
            # Show first 8 chars if it's long, else mask completely
            if len(value) > redact_length:
                return f"{value[:redact_length]}...{REDACTED}"
            return REDACTED
    
    return value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a dictionary by masking sensitive values.
    
    Args:
        data: Dictionary that might contain secrets
        
    Returns:
        New dictionary with secrets masked
    """
    sensitive_keys = {
        'token', 'bot_token', 'telegram_bot_token',
        'password', 'passwd', 'pwd', 
        'secret', 'api_key', 'apikey',
        'authorization', 'auth', 'credentials',
        'channel_id', 'chat_id', 'user_id'
    }
    
    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            if isinstance(value, str):
                sanitized[key] = sanitize_string(value)
            elif isinstance(value, int):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_dict(v) if isinstance(v, dict) else v for v in value]
        else:
            sanitized[key] = value
    
    return sanitized


def safe_log(level: int, message: str, **kwargs) -> None:
    """
    Log a message safely by sanitizing any included data.
    
    Args:
        level: Logging level (e.g., logging.INFO)
        message: Log message
        **kwargs: Additional arguments to sanitize
    """
    sanitized_kwargs = sanitize_dict(kwargs)
    logger.log(level, message, **sanitized_kwargs)


def validate_env_vars() -> List[str]:
    """
    Validate that no secrets are directly exposed in environment.
    
    Returns:
        List of warnings if issues found
    """
    warnings = []
    
    # Check for common mistakes
    env_vars_to_check = ['TELEGRAM_BOT_TOKEN', 'API_KEY', 'SECRET_KEY', 'PASSWORD']
    
    for var in env_vars_to_check:
        value = os.getenv(var)
        if value and (value.startswith('YOUR_') or value.startswith('your_')):
            logger.warning(f"⚠️  {var} not configured - using placeholder")
            warnings.append(f"{var} not set to real value")
    
    return warnings
