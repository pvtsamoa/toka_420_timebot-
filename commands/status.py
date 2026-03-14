import os
import logging
import datetime as dt
from html import escape
from telegram.constants import ParseMode
from services.ritual import kiss_anchor
from services.navigator_blessing import get_blessing

logger = logging.getLogger(__name__)


def _fmt_delta(delta: dt.timedelta) -> str:
    """Format timedelta as human-readable string."""
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


def _get_jobqueue(context):
    try:
        return context.application.job_queue if context.application else None
    except Exception:
        return None


def _count_jobs(context):
    """
    Count scheduled jobs.
    Prefers APScheduler (Windows-safe path), falls back to PTB JobQueue.
    Returns: (scheduler_name, total_jobs, hub_jobs)
    """
    # APScheduler path
    sched = _get_apscheduler(context)
    if sched:
        try:
            jobs = sched.get_jobs()
            hub_jobs = [j for j in jobs if (getattr(j, "id", "") or "").startswith("global_420")]
            return "APScheduler", len(jobs), len(hub_jobs)
        except Exception as e:
            logger.warning("Error counting APScheduler jobs: %s", e)

    # PTB JobQueue path (legacy)
    jq = _get_jobqueue(context)
    if jq:
        try:
            jobs = jq.jobs()
            hub_jobs = [j for j in jobs if (getattr(j, "name", "") or "").startswith("global_420")]
            return "PTB JobQueue", len(jobs), len(hub_jobs)
        except Exception as e:
            logger.warning("Error counting JobQueue jobs: %s", e)

    return "none", 0, 0


def _next_ritual(context):
    """
    Find the soonest scheduled 4:20 ritual.
    Prefers APScheduler, falls back to PTB JobQueue.
    Returns: (scheduler_name, hub_identifier, next_run_datetime_utc)
    """
    # APScheduler path
    sched = _get_apscheduler(context)
    if sched:
        try:
            jobs = sched.get_jobs()
            hub_jobs = [j for j in jobs if (getattr(j, "id", "") or "").startswith("global_420")]
            if not hub_jobs:
                return "APScheduler", None, None

            # next_run_time may be tz-aware. Normalize to UTC for display.
            nxt_job = min(
                (j for j in hub_jobs if getattr(j, "next_run_time", None) is not None),
                key=lambda j: j.next_run_time,
                default=None,
            )
            if not nxt_job:
                return "APScheduler", None, None

            nxt = nxt_job.next_run_time
            # Ensure UTC
            if nxt.tzinfo is None:
                nxt = nxt.replace(tzinfo=dt.timezone.utc)
            else:
                nxt = nxt.astimezone(dt.timezone.utc)

            hub_id = getattr(nxt_job, "id", None) or getattr(nxt_job, "name", None)
            return "APScheduler", hub_id, nxt
        except Exception as e:
            logger.exception("Error getting next ritual from APScheduler: %s", e)
            return "APScheduler", None, None

    # PTB JobQueue path (legacy)
    jq = _get_jobqueue(context)
    if jq:
        try:
            jobs = jq.jobs()
            next_times = [
                j.next_t
                for j in jobs
                if j and getattr(j, "name", "") and (j.name or "").startswith("global_420") and getattr(j, "next_t", None)
            ]
            if not next_times:
                return "PTB JobQueue", None, None

            nxt = min(next_times)
            hub = next((j.name for j in jobs if getattr(j, "next_t", None) == nxt), None)

            # JobQueue next_t is usually tz-aware; normalize to UTC
            if nxt.tzinfo is None:
                nxt = nxt.replace(tzinfo=dt.timezone.utc)
            else:
                nxt = nxt.astimezone(dt.timezone.utc)

            return "PTB JobQueue", hub, nxt
        except Exception as e:
            logger.exception("Error getting next ritual from JobQueue: %s", e)
            return "PTB JobQueue", None, None

    return "none", None, None


async def status(update, context):
    """Show bot health, scheduler status, price updates, and next ritual."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Status command requested (user: %s)", user_id)
    msg = update.effective_message
    if not msg:
        return

    try:
        token = os.getenv("DEFAULT_TOKEN", "weedcoin").lower()
        anchor = kiss_anchor(token)

        sched_name, total_jobs, hub_jobs = _count_jobs(context)
        next_sched_name, hub_id, nxt = _next_ritual(context)

        now = dt.datetime.now(dt.timezone.utc)
        nxt_txt = f"{nxt:%H:%M} UTC (in {_fmt_delta(nxt - now)})" if nxt else "Not scheduled"
        hub_txt = f" | {hub_id}" if hub_id else ""

        blessing = get_blessing()

        message = (
            "<b>Navigator Log - Toka v1</b>\n"
            "----------------------------------------\n\n"
            "<b>BOT HEALTH</b>\n"
            "Status: Online\n\n"
            "<b>SCHEDULER</b>\n"
            f"Engine: {escape(sched_name)}\n"
            f"Jobs scheduled: {hub_jobs} hub jobs (total {total_jobs})\n\n"
            "<b>PRICE ANCHOR</b>\n"
            f"Token: {escape(token.upper())}\n"
            f"{escape(anchor)}\n\n"
            "<b>NEXT RITUAL</b>\n"
            f"Engine: {escape(next_sched_name)}\n"
            f"Time: {escape(nxt_txt + hub_txt)}\n"
            "Frequency: Daily (04:20 local per timezone, rolling global)\n\n"
            "----------------------------------------\n"
            "<b>Navigator's Blessing</b>\n"
            f"{escape(blessing)}\n\n"
            "Use /token [symbol] for detailed charts\n"
            "Use /news for market updates"
        )

        await msg.reply_text(message, parse_mode=ParseMode.HTML)
        logger.info("Status sent to user %s", user_id)

    except Exception as e:
        logger.exception("Error in status command: %s", e)
        await msg.reply_text("Error generating status. Try again later.")
