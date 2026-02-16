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


async def ritual_call(context):
    """
    Executes the 4:20 ritual for a TIMEZONE job.

    context.job.data must include:
      - tz: str
      - hubs: list[hub_dict] where each hub_dict includes:
          - hub: str
          - tier: str
          - cities: list[str]
          - tz: str
    Scheduler chooses the TIMEZONE; this function rotates which HUB and CITY gets the blessing.
    """
    try:
        payload = getattr(context, "job", None).data if getattr(context, "job", None) else None
        if not isinstance(payload, dict):
            logger.error("Ritual payload missing or invalid (context.job.data).")
            return

        tz_name = payload.get("tz")
        hubs = payload.get("hubs") or []
        if not tz_name or not isinstance(hubs, list) or not hubs:
            logger.error("Ritual payload must include tz and non-empty hubs list. payload=%s", payload)
            return

        # Global token override (optional)
        token_id = (
            context.application.bot_data.get("token_override")
            if getattr(context, "application", None)
            else None
        ) or os.getenv("DEFAULT_TOKEN", "weedcoin")

        chat_id = os.getenv("TELEGRAM_GLOBAL_CHAT_ID")
        if not chat_id:
            logger.error("TELEGRAM_GLOBAL_CHAT_ID not set. Cannot send ritual for tz=%s", tz_name)
            return

        day_idx = _date_index_for_tz(tz_name)

        # Policy B: rotate hubs daily within the timezone (everyone eats)
        chosen_hub = _pick_rotating(hubs, day_idx)
        if not isinstance(chosen_hub, dict):
            logger.error("Chosen hub invalid. tz=%s chosen=%s", tz_name, chosen_hub)
            return

        cities = chosen_hub.get("cities") or []
        chosen_city = _pick_rotating(cities, day_idx)

        hub_id = chosen_hub.get("hub", "hub")
        tier = chosen_hub.get("tier", "")

        logger.info(
            "Ritual start tz=%s hub=%s tier=%s city=%s token=%s",
            tz_name,
            hub_id,
            tier,
            chosen_city,
            token_id,
        )

        # Build message using new hub model
        text = build_ritual_text(
            chosen_hub,
            token_id=token_id,
            city=chosen_city,
            tier=tier,
        )

        await context.bot.send_message(chat_id=chat_id, text=text)

        logger.info("Ritual sent tz=%s hub=%s city=%s", tz_name, hub_id, chosen_city)

    except Exception as e:
        logger.exception("Ritual failed: %s", e)
