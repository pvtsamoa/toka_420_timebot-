import xml.etree.ElementTree as ET
import requests
import random
import logging
from telegram import Update
from telegram.ext import ContextTypes

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
        "link": "https://www.projectcbd.org/"
    },
    {
        "title": "Regenerative Agriculture & Cannabis Cultivation",
        "link": "https://www.regenerativeorganic.org/"
    },
    {
        "title": "Cannabis Research Database (NIH/NLM)",
        "link": "https://www.ncbi.nlm.nih.gov/research/cannabinoid/"
    },
    {
        "title": "Endocannabinoid System & Human Health",
        "link": "https://pubmed.ncbi.nlm.nih.gov/?term=endocannabinoid+system"
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
            logger.debug(f"No items in study feed: {url}")
            return None
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()[:100]
        if not title or not link:
            logger.debug(f"Invalid item in study feed: {url}")
            return None
        return title, link, description
    except requests.Timeout:
        logger.warning(f"Timeout fetching study feed: {url}")
        return None
    except requests.RequestException as e:
        logger.warning(f"Request error fetching study feed {url}: {e}")
        return None
    except ET.ParseError as e:
        logger.warning(f"XML parse error in study feed {url}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error fetching study feed {url}: {e}")
        return None

async def studies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and send cannabis research & health awareness content."""
    user_id = update.effective_user.id
    logger.info(f"Studies command requested (user: {user_id})")
    
    # Try to fetch from research feeds
    for url in STUDY_FEEDS:
        hit = _fetch_study(url)
        if hit:
            title, link, desc = hit
            lines = [
                "ðŸ”¬ Cannabis Research & Awareness",
                "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                f"â€¢ {title}",
                f"ðŸ“– {desc}..." if desc else "",
                f"ðŸ”— {link}",
            ]
            logger.info(f"Sent study article (user: {user_id})")
            await update.message.reply_text("\n".join(filter(None, lines)))
            return

    # Fallback: rotate through curated resources
    resource = random.choice(FALLBACK_RESOURCES)
    lines = [
        "ðŸ”¬ Cannabis Research & Whole Plant Awareness",
        "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        f"â€¢ {resource['title']}",
        f"ðŸ”— {resource['link']}",
        "",
        "Topics: Health benefits â€¢ Nutrition â€¢ Endocannabinoid system â€¢ Land regeneration â€¢ Phytochemistry",
    ]
    logger.info(f"Sent fallback resource (user: {user_id})")
    await update.message.reply_text("\n".join(lines))
