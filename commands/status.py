"""
/status command — Show bot health, mode, and next 4:20
"""
import logging
import datetime as dt
from services.navigator_blessing import get_blessing
from services.market_snapshot import format_market_snapshot_lines

logger = logging.getLogger(__name__)


def _fmt_delta(delta: dt.timedelta) -> str:
    secs = int(delta.total_seconds())
    if secs < 0:
        secs = 0
    h, r = divmod(secs, 3600)
    m, _ = divmod(r, 60)
    return f"{h}h {m}m"


def _get_apscheduler(context):
    try:
        return context.application.bot_data.get("apscheduler") if context.application else None
    except Exception:
        return None


def _next_fire_time(context):
    sched = _get_apscheduler(context)
    if not sched:
        return None, 0
    try:
        jobs = sched.get_jobs()
        if not jobs:
            return None, 0
        next_job = min(
            (j for j in jobs if getattr(j, "next_run_time", None) is not None),
            key=lambda j: j.next_run_time,
            default=None,
        )
        if not next_job:
            return None, len(jobs)
        nxt = next_job.next_run_time
        if nxt.tzinfo is None:
            nxt = nxt.replace(tzinfo=dt.timezone.utc)
        else:
            nxt = nxt.astimezone(dt.timezone.utc)
        return nxt, len(jobs)
    except Exception as e:
        logger.warning("Error getting next fire time: %s", e)
        return None, 0


async def status(update, context):
    user_id = update.effective_user.id
    logger.info("Status command requested (user: %s)", user_id)

    try:
        market_lines = format_market_snapshot_lines()
        market_block = "\n".join(market_lines)

        mode = context.application.bot_data.get("420_mode", "both")
        hub_count = len(context.application.bot_data.get("all_hubs", []))
        nxt, job_count = _next_fire_time(context)

        now = dt.datetime.now(dt.timezone.utc)
        nxt_txt = f"{nxt:%H:%M} UTC (in {_fmt_delta(nxt - now)})" if nxt else "Not scheduled"

        mode_label = {
            "am": "AM only (4:20 AM)",
            "pm": "PM only (4:20 PM)",
            "both": "AM + PM (power user)",
        }.get(mode, mode)

        blessing = get_blessing()

        message = (
            "Toka Pulse\n"
            "----------------------------------------\n"
            "\n"
            "BOT\n"
            "Status: Online\n"
            "\n"
            "IT'S 4:20 SOMEWHERE\n"
            f"Mode: {mode_label}\n"
            f"Hubs loaded: {hub_count} timezones\n"
            f"Checker jobs: {job_count} (fires every hour at :20 and :50)\n"
            "\n"
            "MARKET SNAPSHOT\n"
            f"{market_block}\n"
            "\n"
            "NEXT CHECK\n"
            f"Time: {nxt_txt}\n"
            "The bot checks every hour for which timezone just hit 4:20.\n"
            "\n"
            "----------------------------------------\n"
            "Blessing\n"
            f"{blessing}\n"
            "\n"
            "Use /news for cannabis + crypto headlines"
        )

        await update.message.reply_text(message)
        logger.info("Status sent to user %s", user_id)

    except Exception as e:
        logger.exception("Error in status command: %s", e)
        await update.message.reply_text("Error generating status. Try again later.")
