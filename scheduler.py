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

    enabled = [h for h in hubs if h.get("enabled", True) is True]

    logger.info("Loaded %d hubs (%d enabled)", len(hubs), len(enabled))
    return enabled


def find_420_hubs_now(hubs: list, mode: str = "both") -> list:
    """
    Find which hubs are currently at 4:20.

    Args:
        hubs: list of hub dicts from hubs.json
        mode: "am" = only 4:20 AM fires
              "pm" = only 4:20 PM fires
              "both" = AM and PM (power user)

    Checks every hub's timezone. If their local time is
    4:20 AM and/or 4:20 PM (depending on mode), they match.
    """
    now_utc = dt.datetime.now(dt.timezone.utc)
    matching = []

    # Which hours count based on mode
    if mode == "am":
        target_hours = {4}
    elif mode == "pm":
        target_hours = {16}
    else:
        target_hours = {4, 16}

    for hub in hubs:
        tz_name = hub.get("tz")
        if not tz_name:
            continue

        try:
            tz = pytz.timezone(tz_name)
            local_now = now_utc.astimezone(tz)

            # Check if local time is 4:20 or 16:20
            if local_now.hour in target_hours and local_now.minute == 20:
                # Add context about AM or PM
                period = "AM" if local_now.hour == 4 else "PM"
                # Make a copy so we don't mutate the original
                hub_copy = dict(hub)
                hub_copy["_period"] = period
                hub_copy["_local_time"] = local_now.strftime("%I:%M %p")
                matching.append(hub_copy)
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
    Schedule the global 4:20 checker.

    Fires at :20 every hour (for full-hour timezones)
    and at :50 every hour (for half-hour timezones like India +5:30).

    When it fires, it checks which timezones are currently
    at 4:20 and sends rituals for those zones.
    """
    hubs = load_hubs()

    if app:
        app.bot_data["all_hubs"] = hubs
        # Default mode is "both" (AM + PM).
        if "420_mode" not in app.bot_data:
            app.bot_data["420_mode"] = "both"

    from apscheduler.triggers.cron import CronTrigger

    async def _run():
        """Find who's at 4:20 right now and fire their ritual."""
        current_hubs = app.bot_data.get("all_hubs", [])
        mode = app.bot_data.get("420_mode", "both")
        matching = find_420_hubs_now(current_hubs, mode=mode)

        if not matching:
            logger.debug("No timezone at 4:20 right now (mode=%s)", mode)
            return

        logger.info(
            "4:20 CHECK — %d hub(s) hitting 4:20 right now (mode=%s)",
            len(matching),
            mode,
        )

        # NEW: Send ONE ritual with ALL matching hubs
        # ritual_time.py will handle selecting 3 hubs (major/minor/growing)
        payload = {
            "all_hubs": matching,
        }

        ctx = _build_ptb_context(app, payload)

        try:
            if inspect.iscoroutinefunction(callback):
                await callback(ctx)
            else:
                callback(ctx)
            logger.info("Ritual fired for %d hubs at 4:20", len(matching))
        except Exception as e:
            logger.exception("Ritual failed: %s", e)

    def _fire():
        """Bridge from APScheduler sync call to async."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_run())
        except RuntimeError:
            asyncio.run(_run())

    # Job 1: Fire at :20 every hour (catches full-hour UTC offsets)
    job_main = scheduler.add_job(
        _fire,
        CronTrigger(minute=20),
        id="global_420_main",
        name="global_420_main",
        replace_existing=True,
    )

    # Job 2: Fire at :50 every hour (catches half-hour UTC offsets like India +5:30)
    job_half = scheduler.add_job(
        _fire,
        CronTrigger(minute=50),
        id="global_420_half",
        name="global_420_half",
        replace_existing=True,
    )

    logger.info(
        "Global 4:20 checker scheduled | %d hubs | mode=%s",
        len(hubs),
        app.bot_data.get("420_mode", "both"),
    )
    logger.info(
        "  :20 job next=%s",
        getattr(job_main, "next_run_time", None),
    )
    logger.info(
        "  :50 job next=%s (half-hour zones)",
        getattr(job_half, "next_run_time", None),
    )
