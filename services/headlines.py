import logging
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)

CRYPTO_NEWS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.theblock.co/rss.xml",
]

CANNABIS_NEWS_FEEDS = [
    "https://mjbizdaily.com/feed/",
    "https://www.marijuanamoment.net/feed/",
    "https://hightimes.com/feed/",
    "https://www.greenmarketreport.com/feed/",
]


def _fetch_one(url: str):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Toka420Bot/1.0"})
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("./channel")
        if channel is None:
            return None

        item = channel.find("item")
        if item is None:
            return None

        source = (channel.findtext("title") or "").strip() or "Unknown Source"
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not link:
            link_el = item.find("link")
            if link_el is not None and link_el.attrib.get("href"):
                link = link_el.attrib["href"].strip()

        if not title or not link:
            return None
        return source, title, link
    except Exception as e:
        logger.debug("headline fetch failed for %s: %s", url, e)
        return None


def get_latest_cannabis_crypto_headline() -> str:
    """Return one latest headline line with source and link."""
    # Favor cannabis culture sources first, then crypto market sources.
    for url in CANNABIS_NEWS_FEEDS + CRYPTO_NEWS_FEEDS:
        hit = _fetch_one(url)
        if hit:
            source, title, link = hit
            return f"{title}\nSource: {source}\n{link}"

    return "No headline available right now."
