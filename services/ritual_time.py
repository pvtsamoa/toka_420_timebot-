import os
import logging
import datetime as dt
import pytz

from services.ritual import build_ritual_text

logger = logging.getLogger(__name__)
dispatch_logger = logging.getLogger("toka.dispatch")

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
    Execute the 4:20 ritual for a timezone group.

    context.job.data must include:
      - tz:   str        — IANA timezone name
      - hubs: list[dict] — hub dicts for this timezone
    """
    try:
        payload = getattr(context, "job", None).data if getattr(context, "job", None) else None
        if not isinstance(payload, dict):
            logger.error("Ritual payload missing or invalid (context.job.data).")
            return

        tz_name = payload.get("tz")
        hubs = payload.get("hubs") or []
        if not tz_name or not isinstance(hubs, list) or not hubs:
            logger.error("Ritual payload must include tz and non-empty hubs. payload=%s", payload)
            return

        chat_id = os.getenv("TELEGRAM_GLOBAL_CHAT_ID")
        if not chat_id:
            logger.error("TELEGRAM_GLOBAL_CHAT_ID not set. tz=%s", tz_name)
            return

        day_idx    = _date_index_for_tz(tz_name)
        chosen_hub = _pick_rotating(hubs, day_idx)
        if not isinstance(chosen_hub, dict):
            logger.error("Chosen hub invalid. tz=%s chosen=%s", tz_name, chosen_hub)
            return

        hub_id  = chosen_hub.get("hub", "hub")
        display = chosen_hub.get("display") or tz_name

        logger.info("Ritual start tz=%s hub=%s", tz_name, hub_id)

        text = build_ritual_text(chosen_hub, city=display)

        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            dispatch_logger.error(
                "dispatch_failure side=telegram tz=%s hub=%s chat_id=%s error=%s",
                tz_name, hub_id, chat_id, e,
            )
            raise

        logger.info("Ritual sent tz=%s hub=%s display=%s", tz_name, hub_id, display)

    except Exception as e:
        logger.exception("Ritual failed: %s", e)
