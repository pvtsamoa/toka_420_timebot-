import xml.etree.ElementTree as ET
import requests
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

CRYPTO_NEWS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.theblock.co/rss.xml",
]

CANNABIS_NEWS = [
    "https://mjbizdaily.com/feed/",
    "https://www.marijuanamoment.net/feed/",
    "https://hightimes.com/feed/",
    "https://www.greenmarketreport.com/feed/",
]


def _fetch_one(url: str):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Toka420Bot/1.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        channel = root.find("./channel")
        if channel is None:
            logger.debug("No RSS channel found for feed: %s", url)
            return None
        chan_title = (channel.findtext("title") or "").strip()
        item = channel.find("item")
        if item is None:
            logger.debug("No items in feed: %s", url)
            return None
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
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


def _collect_headlines(feeds, limit: int = 2):
    hits = []
    for url in feeds:
        result = _fetch_one(url)
        if result:
            hits.append(result)
        if len(hits) >= limit:
            break
    return hits


def _reply_target(update: Update):
    return update.effective_message


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send relevant cannabis and crypto headlines."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("News command requested (user: %s)", user_id)

    msg = _reply_target(update)

    try:
        crypto_hits = _collect_headlines(CRYPTO_NEWS, limit=2)
        cannabis_hits = _collect_headlines(CANNABIS_NEWS, limit=2)

        if not crypto_hits and not cannabis_hits:
            if msg:
                await msg.reply_text("Could not fetch cannabis/crypto headlines right now. Try again shortly.")
            logger.warning("Could not fetch any headlines")
            return

        lines = ["Cannabis x Crypto Headlines", ""]

        lines.append("Crypto")
        if crypto_hits:
            for source, title, link in crypto_hits:
                lines.append(f"- {title}")
                lines.append(f"  Source: {source}")
                lines.append(f"  {link}")
        else:
            lines.append("- No crypto headlines available")

        lines.append("")
        lines.append("Cannabis Culture / Industry")
        if cannabis_hits:
            for source, title, link in cannabis_hits:
                lines.append(f"- {title}")
                lines.append(f"  Source: {source}")
                lines.append(f"  {link}")
        else:
            lines.append("- No cannabis headlines available")

        lines.append("")
        lines.append("Run /news again for a fresh pull")
        message = "\n".join(lines)

        if msg:
            await msg.reply_text(message)

        logger.info(
            "Sent headlines to user %s (crypto=%d, cannabis=%d)",
            user_id,
            len(crypto_hits),
            len(cannabis_hits),
        )

    except Exception as e:
        logger.exception("Error in news command: %s", e)
        if msg:
            await msg.reply_text("Error fetching news. Try again later.")
