import os
import logging
import datetime as dt
import pytz

from services.ritual import build_ritual_text

logger = logging.getLogger(__name__)


_EPOCH = dt.date(2024, 1, 1)


def _date_index_for_tz(tz_name: str) -> int:
    tz = pytz.timezone(tz_name)
    today = dt.datetime.now(tz).date()
    return (today - _EPOCH).days


def _pick_rotating(items, idx: int):
    if not items:
        return None
    return items[idx % len(items)]


def select_three_hubs(all_hubs: list, day_idx: int) -> dict:
    """
    Select 3 hubs from available hubs: one major, one minor, one growing.

    Args:
        all_hubs: List of hub dicts currently at 4:20
        day_idx: Daily rotation index

    Returns:
        dict with keys: major, minor, growing (each a hub dict or None)
    """
    # Group hubs by tier
    by_tier = {"major": [], "minor": [], "growing": []}
    for hub in all_hubs:
        tier = hub.get("tier", "").lower()
        if tier in by_tier:
            by_tier[tier].append(hub)

    # Pick one from each tier using rotation
    selected = {}
    for tier_name in ["major", "minor", "growing"]:
        hubs_in_tier = by_tier[tier_name]
        if hubs_in_tier:
            # Rotate daily which hub from this tier gets picked
            selected[tier_name] = _pick_rotating(hubs_in_tier, day_idx)
        else:
            selected[tier_name] = None
            logger.warning("No %s tier hubs available at 4:20", tier_name)

    return selected


async def ritual_call(context):
    """
    Executes the 4:20 ritual with 3 hubs (major/minor/growing).

    context.job.data must include:
      - all_hubs: list[hub_dict] of all hubs currently at 4:20

    This function selects 3 hubs (one from each tier), picks a city from each,
    and builds ONE compact ritual message featuring all 3.
    """
    try:
        payload = getattr(context, "job", None).data if getattr(context, "job", None) else None
        if not isinstance(payload, dict):
            logger.error("Ritual payload missing or invalid (context.job.data).")
            return

        all_hubs = payload.get("all_hubs") or []
        if not isinstance(all_hubs, list) or not all_hubs:
            logger.error("Ritual payload must include non-empty all_hubs list. payload=%s", payload)
            return

        chat_id = os.getenv("TELEGRAM_GLOBAL_CHAT_ID")
        if not chat_id:
            logger.error("TELEGRAM_GLOBAL_CHAT_ID not set. Cannot send ritual.")
            return

        # Use UTC date for global rotation (consistent across all timezones)
        now_utc = dt.datetime.now(dt.timezone.utc)
        day_idx = (now_utc.date() - _EPOCH).days

        # Select 3 hubs: one major, one minor, one growing
        selected = select_three_hubs(all_hubs, day_idx)

        # Build list of hubs with their chosen cities
        ritual_hubs = []
        for tier_name in ["major", "minor", "growing"]:
            hub = selected.get(tier_name)
            if hub:
                cities = hub.get("cities") or []
                chosen_city = _pick_rotating(cities, day_idx)
                ritual_hubs.append({
                    "hub": hub,
                    "city": chosen_city,
                    "tier": tier_name,
                })

        if not ritual_hubs:
            logger.error("No hubs selected for ritual (empty ritual_hubs)")
            return

        logger.info(
            "Ritual start — %d hubs selected: %s",
            len(ritual_hubs),
            ", ".join(f"{rh['city']} ({rh['tier']})" for rh in ritual_hubs if rh.get('city'))
        )

        # Build message featuring all 3 hubs
        text = build_ritual_text(ritual_hubs)

        await context.bot.send_message(chat_id=chat_id, text=text)

        # Update statistics in persistence
        persistence = (
            context.application.bot_data.get("persistence")
            if getattr(context, "application", None)
            else None
        )
        if persistence:
            persistence.increment("ritual_count")
            # Store all 3 timezones for stats
            tzs = [rh["hub"].get("tz") for rh in ritual_hubs if rh.get("hub")]
            persistence.set("last_ritual_tzs", tzs)

        logger.info(
            "Ritual sent — %s",
            ", ".join(f"{rh['city']} ({rh['tier']})" for rh in ritual_hubs if rh.get('city'))
        )

    except Exception as e:
        logger.exception("Ritual failed: %s", e)
