import xml.etree.ElementTree as ET
import requests
import logging
import time
from telegram import Update
from telegram.ext import ContextTypes
from config import SETTINGS

logger = logging.getLogger(__name__)

# Rate limiting
_rate_limit_cache = {}
RATE_LIMIT_SECONDS = 3

# News category sources
CRYPTO_NEWS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://bitcoinmagazine.com/feed/rss",
    "https://cryptoslate.com/feed/",
]

MARKET_NEWS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.reuters.com/reuters/businessNews",
]

# Regional fallback feeds
REGIONAL_FEEDS = {
    "apac": [
        "https://ambcrypto.com/feed/",
        "https://www.newsbtc.com/feed/",
        "https://cointelegraph.com/rss",
    ],
    "emea": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptonews.com/news/feed/",
        "https://coinjournal.net/news/feed/",
    ],
    "amer": [
        "https://decrypt.co/feed",
        "https://bitcoinmagazine.com/feed/rss",
        "https://cryptoslate.com/feed/",
    ],
}

# Track user call counts for rotation
_user_calls = {}


def _fetch_one(url: str):
    """Fetch the first valid item from an RSS feed."""
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Toka420Bot/1.0"})
        r.raise_for_status()

        root = ET.fromstring(r.content)

        # RSS: <rss><channel>...
        channel = root.find("./channel")
        if channel is None:
            # Atom feeds sometimes look different; fail gracefully
            logger.debug("No RSS channel found for feed: %s", url)
            return None

        chan_title = (channel.findtext("title") or "").strip()
        item = channel.find("item")
        if item is None:
            logger.debug("No items in feed: %s", url)
            return None

        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()

        # Some feeds use <link href="..."> or have whitespace/newlines
        if not link:
            link_el = item.find("link")
            if link_el is not None and link_el.attrib.get("href"):
                link = link_el.attrib["href"].strip()

        if not title or not link:
            logger.debug("Invalid item in feed: %s", url)
            return None

        return chan_title, title, link

    except requests.Timeout:
        logger.warning("Timeout fetching feed: %s", url)
        return None
    except requests.RequestException as e:
        logger.warning("Request error fetching feed %s: %s", url, e)
        return None
    except ET.ParseError as e:
        logger.warning("XML parse error in feed %s: %s", url, e)
        return None
    except Exception as e:
        logger.exception("Unexpected error fetching feed %s: %s", url, e)
        return None


def _get_category_cycle(user_id: int) -> str:
    """Rotate through 2 categories per user call (crypto â†’ market)."""
    call_count = _user_calls.get(user_id, 0)
    _user_calls[user_id] = call_count + 1
    return ["crypto", "market"][call_count % 2]


def _reply_target(update: Update):
    return update.effective_message


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send rotating news: Crypto â†’ Markets, with optional regional fallback."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("News command requested (user: %s)", user_id)

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

    try:
        category = _get_category_cycle(int(user_id) if user_id != "unknown" else 0)

        if category == "crypto":
            feeds = CRYPTO_NEWS
            emoji = "ðŸ’°"
            title = "Cryptocurrency News"
        else:
            feeds = MARKET_NEWS
            emoji = "ðŸ“ˆ"
            title = "Market and Finance News"

        result = None
        for url in feeds:
            result = _fetch_one(url)
            if result:
                break

        if not result:
            scope = (getattr(SETTINGS, "TELEGRAM_SCOPE", None) or "all").lower()
            fallback_feeds = REGIONAL_FEEDS.get(scope, [])
            for url in fallback_feeds:
                result = _fetch_one(url)
                if result:
                    break

        if not result:
            if msg:
                await msg.reply_text(
                    f"âš ï¸ Could not fetch {title.lower()} right now.\n\nTry again in a few moments.",
                    parse_mode="Markdown",
                )
            logger.warning("Could not fetch any news for category %s", category)
            return

        chan_title, article_title, link = result

        message = f"""
{emoji} **{title}**

**{article_title}**

ðŸ“° Source: {chan_title}
ðŸ”— [Read more]({link})

--------------------
*Call `/news` again for the next category*
*Categories rotate: Crypto â†’ Markets*
"""

        if msg:
            await msg.reply_text(message, parse_mode="Markdown")

        logger.info("Sent %s news to user %s: %s", category, user_id, article_title[:80])

    except Exception as e:
        logger.exception("Error in news command: %s", e)
        if msg:
            await msg.reply_text("âš ï¸ Error fetching news. Try again later.", parse_mode="Markdown")
