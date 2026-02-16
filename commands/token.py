import logging
import os
import time
from telegram import Update
from telegram.ext import ContextTypes
from services.dexscreener import get_anchor

logger = logging.getLogger(__name__)

# Rate limiting
_rate_limit_cache = {}
RATE_LIMIT_SECONDS = 3


def _reply_target(update: Update):
    # Always prefer effective_message; update.message can be None in some contexts.
    return update.effective_message


async def token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show price movement and liquidity for a token (default: Weedcoin)."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    msg = _reply_target(update)

    # Rate limiting
    now = time.time()
    if user_id in _rate_limit_cache:
        elapsed = now - _rate_limit_cache[user_id]
        if elapsed < RATE_LIMIT_SECONDS:
            if msg:
                await msg.reply_text(
                    f"⏱️ Please wait {RATE_LIMIT_SECONDS - int(elapsed)} seconds before requesting again."
                )
            logger.info("Rate limited user %s (elapsed: %.1fs)", user_id, elapsed)
            return
    _rate_limit_cache[user_id] = now

    # Get token symbol from args or default
    if context.args and context.args[0].strip():
        token_symbol = context.args[0].strip().lower()

        # Input validation
        if len(token_symbol) > 100:
            if msg:
                await msg.reply_text("âŒ Token too long (max 100 chars)")
            logger.warning("Token too long: %s (user: %s)", token_symbol, user_id)
            return

        if not all(c.isalnum() or c in "-_" for c in token_symbol):
            if msg:
                await msg.reply_text("âŒ Invalid token format. Use alphanumeric, dash, or underscore only")
            logger.warning("Invalid token format: %s (user: %s)", token_symbol, user_id)
            return
    else:
        token_symbol = os.getenv("DEFAULT_TOKEN", "weedcoin").lower()

    logger.info("Token price query for: %s (user: %s)", token_symbol, user_id)

    try:
        anchor = get_anchor(token_symbol)

        if not anchor:
            if msg:
                await msg.reply_text(
                    f"âŒ Could not find token: `{token_symbol}`\n\n"
                    f"Try `/token weedcoin` or `/token btc`",
                    parse_mode="Markdown",
                )
            logger.warning("Token not found: %s", token_symbol)
            return

        symbol = (anchor.get("symbol", "?") or "?").upper()
        price = anchor.get("price", "?")
        change24 = anchor.get("change24", "+/-0.00%")
        vol24 = anchor.get("vol24", "$0")
        dex = (anchor.get("dex", "") or "").upper()

        message = f"""
ðŸ’° **{symbol}** Price

ðŸ”¢ **Current Price**
`{price}`

ðŸ“ˆ **24h Movement**
{change24}

ðŸ’§ **24h Liquidity / Volume**
{vol24}

ðŸª **Exchange**: {dex}

--------------------
*Run `/token` again for fresh data*
*Use `/news` for market updates*
"""

        if msg:
            await msg.reply_text(message, parse_mode="Markdown")
        logger.info("Sent price data for %s (user: %s)", symbol, user_id)

    except Exception as e:
        logger.exception("Error fetching token data for %s: %s", token_symbol, e)
        if msg:
            await msg.reply_text("âš ï¸ Error fetching price data. Try again later.", parse_mode="Markdown")


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check endpoint to verify bot is running."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Health check requested by user %s", user_id)

    msg = _reply_target(update)
    if msg:
        await msg.reply_text("ðŸŸ¢ Toka is healthy and running âœ¨")
