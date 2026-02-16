import os
import json
import pytz
import datetime as dt
import logging
import asyncio
import inspect
from types import SimpleNamespace

logger = logging.getLogger(__name__)

# scheduler.py lives at project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# All bot JSON config lives in /media
HUBS_PATH = os.path.join(PROJECT_ROOT, "media", "hubs.json")


def load_hubs():
    """Load hub definitions from hubs.json."""
    logger.info("Loading hubs from: %s", HUBS_PATH)

    try:
        with open(HUBS_PATH, "r", encoding="utf-8") as f:
            hubs = json.load(f)
    except FileNotFoundError:
        logger.error("hubs.json not found at %s", HUBS_PATH)
        raise ValueError(f"Missing {HUBS_PATH}")
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in hubs.json: %s", e)
        raise ValueError(f"Invalid JSON in {HUBS_PATH}") from e

    if not isinstance(hubs, list):
        raise ValueError("hubs.json must be a JSON list")

    # allow enabled=false
    enabled = [h for h in hubs if h.get("enabled", True) is True]

    logger.info("Loaded %d hubs (%d enabled)", len(hubs), len(enabled))
    return enabled


def find_420_hubs_now(hubs: list) -> list:
    """
    Find which hubs are currently at 4:20 (AM or PM).
    
    Checks every hub's timezone to see if the local time
    is currently the :20 minute of hour 4 or hour 16.
    Returns list of matching hubs.
    """
    now_utc = dt.datetime.now(dt.timezone.utc)
    matching = []

    for hub in hubs:
        tz_name = hub.get("tz")
        if not tz_name:
            continue

        try:
            tz = pytz.timezone(tz_name)
            local_now = now_utc.astimezone(tz)

            # Check if it's 4:20 AM or 4:20 PM (hour 4 or 16, minute 20)
            if local_now.hour in (4, 16) and local_now.minute == 20:
                hub["_local_hour"] = local_now.hour
                matching.append(hub)
        except Exception as e:
            logger.warning("Error checking timezone %s: %s", tz_name, e)

    return matching


def _build_ptb_context(app, data: dict):
    """Minimal PTB-like CallbackContext shim."""
    return SimpleNamespace(
        job=SimpleNamespace(data=data),
        application=app,
        bot=getattr(app, "bot", None),
    )


def schedule_hourly_420(scheduler, callback, app=None):
    """
    Schedule ONE job that fires every hour at :20.
    
    When it fires, it checks which timezones are currently
    at 4:20 (AM or PM) and sends rituals for those zones.
    """
    hubs = load_hubs()

    # Store hubs in app.bot_data so the callback can access them
    if app:
        app.bot_data["all_hubs"] = hubs

    from apscheduler.triggers.cron import CronTrigger

    async def _run():
        """Find who's at 4:20 right now and fire their ritual."""
        current_hubs = app.bot_data.get("all_hubs", [])
        matching = find_420_hubs_now(current_hubs)

        if not matching:
            logger.debug("No timezone at 4:20 right now")
            return

        # Group matching hubs by timezone (multiple hubs can share a tz)
        tz_groups = {}
        for hub in matching:
            tz = hub.get("tz")
            tz_groups.setdefault(tz, []).append(hub)

        for tz_name, hubs_in_tz in tz_groups.items():
            payload = {
                "tz": tz_name,
                "hubs": hubs_in_tz,
            }

            ctx = _build_ptb_context(app, payload)

            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(ctx)
                else:
                    callback(ctx)
                logger.info("Ritual fired for %s (%d hubs)", tz_name, len(hubs_in_tz))
            except Exception as e:
                logger.exception("Ritual failed for %s: %s", tz_name, e)

    def _fire():
        """Bridge from APScheduler sync call to async."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_run())
        except RuntimeError:
            asyncio.run(_run())

    # Fire every hour at minute :20
    job = scheduler.add_job(
        _fire,
        CronTrigger(minute=20),  # every hour at :20
        id="global_420_check",
        name="global_420_check",
        replace_existing=True,
    )

    logger.info(
        "Global 4:20 checker scheduled (every hour at :20) | %d hubs loaded | next=%s",
        len(hubs),
        getattr(job, "next_run_time", None),
    )
