import asyncio
import xml.etree.ElementTree as ET
import requests
import random
import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.content_policy import sanitize_text

logger = logging.getLogger(__name__)

# Educational RSS feeds on cannabis research, health, nutrition, sustainability
STUDY_FEEDS = [
    "https://www.ncbi.nlm.nih.gov/research/cannabinoid/",
    "https://pubmed.ncbi.nlm.nih.gov/?term=cannabis+health+benefits",
    "https://www.researchgate.net/topic/Cannabis-Health-Benefits",
    "https://www.projectcbd.org/article/feed",
]

# Fallback educational resources
FALLBACK_RESOURCES = [
    {
        "title": "Whole Plant Nutrition & Phytocannabinoid Profiles",
        "link": "https://www.projectcbd.org/",
    },
    {
        "title": "Regenerative Agriculture & Cannabis Cultivation",
        "link": "https://www.regenerativeorganic.org/",
    },
    {
        "title": "Cannabis Research Database (NIH/NLM)",
        "link": "https://www.ncbi.nlm.nih.gov/research/cannabinoid/",
    },
    {
        "title": "Endocannabinoid System & Human Health",
        "link": "https://pubmed.ncbi.nlm.nih.gov/?term=endocannabinoid+system",
    },
]


def _fetch_study(url: str):
    """Fetch a study/article from an RSS feed."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        item = root.find(".//item")
        if item is None:
            logger.debug("No items in study feed: %s", url)
            return None
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()[:100]
        if not title or not link:
            logger.debug("Invalid item in study feed: %s", url)
            return None
        return title, link, description
    except requests.Timeout:
        logger.warning("Timeout fetching study feed: %s", url)
        return None
    except requests.RequestException as e:
        logger.warning("Request error fetching study feed %s: %s", url, e)
        return None
    except ET.ParseError as e:
        logger.warning("XML parse error in study feed %s: %s", url, e)
        return None
    except Exception as e:
        logger.exception("Unexpected error fetching study feed %s: %s", url, e)
        return None


async def studies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and send cannabis research & health awareness content."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Studies command requested (user: %s)", user_id)
    msg = update.effective_message
    if not msg:
        return

    # Try to fetch from research feeds (non-blocking)
    for url in STUDY_FEEDS:
        hit = await asyncio.to_thread(_fetch_study, url)
        if hit:
            title, link, desc = hit
            lines = [
                "Cannabis Research and Awareness",
                "------------------------",
                f"- {sanitize_text(title)}",
                f"Summary: {sanitize_text(desc)}..." if desc else "",
                f"Link: {link}",
            ]
            logger.info("Sent study article (user: %s)", user_id)
            await msg.reply_text("\n".join(filter(None, lines)))
            return

    # Fallback: rotate through curated resources
    resource = random.choice(FALLBACK_RESOURCES)
    lines = [
        "Cannabis Research and Whole Plant Awareness",
        "------------------------",
        f"- {sanitize_text(resource['title'])}",
        f"Link: {resource['link']}",
        "",
        "Topics: Health benefits, nutrition, endocannabinoid system, land regeneration, phytochemistry",
    ]
    logger.info("Sent fallback resource (user: %s)", user_id)
    await msg.reply_text("\n".join(lines))
