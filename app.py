import os
import sys
import logging
import re
import time
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.error import NetworkError, TimedOut
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.config_validator import validate_config
from services.error_handler import on_error
from services.joke_rotation import get_store
from scheduler import schedule_hourly_420
from services.ritual_time import ritual_call

from commands.blessnow import blessnow


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

logger = logging.getLogger("toka.app")
DISPATCH_LOGGER_NAME = "toka.dispatch"

_BOT_TOKEN_RE = re.compile(r"(https://api\.telegram\.org/bot)([^/\s]+)")


class RedactTelegramTokenFilter(logging.Filter):
    """Redact Telegram bot token fragments from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage()
            redacted = _BOT_TOKEN_RE.sub(r"\1<redacted>", rendered)
            if redacted != rendered:
                record.msg  = redacted
                record.args = ()
        except Exception:
            pass
        return True


def configure_logging() -> None:
    os.makedirs(LOG_DIR,  exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(LOG_DIR, "bot.log"), encoding="utf-8"),
        ],
    )

    dispatch_logger = logging.getLogger(DISPATCH_LOGGER_NAME)
    dispatch_logger.setLevel(logging.WARNING)
    dispatch_logger.propagate = False

    if not dispatch_logger.handlers:
        dh = logging.FileHandler(
            os.path.join(LOG_DIR, "dispatch_errors.log"), encoding="utf-8"
        )
        dh.setLevel(logging.WARNING)
        dh.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s")
        )
        dispatch_logger.addHandler(dh)

    # Suppress full Telegram URLs (contain bot token) from httpx/httpcore logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    token_filter = RedactTelegramTokenFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(token_filter)
    for handler in dispatch_logger.handlers:
        handler.addFilter(token_filter)


def validate_env_permissions() -> None:
    """Warn if .env is world-readable. Unix only — no-op on Windows."""
    if os.name == "nt":
        return
    import stat
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    try:
        st = os.stat(env_path)
        if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            logger.warning(
                ".env has insecure permissions — run: chmod 600 .env (current: %o)",
                stat.S_IMODE(st.st_mode),
            )
    except Exception as e:
        logger.warning("Could not check .env permissions: %s", e)


async def set_bot_info(app: Application) -> None:
    try:
        await app.bot.set_my_description(
            "Daily 4:20 Green Hour rituals — blessing, Weedcoin price, crypto update, and a joke."
        )
        await app.bot.set_my_commands([
            BotCommand("blessnow", "Trigger the current Green Hour blessing now"),
        ])
        logger.info("Bot info updated")
    except Exception as e:
        logger.warning("Could not update bot info: %s", e)


def build_app() -> Application:
    logger.info("Building Toka 420 Time Bot...")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    # Windows-safe: disable PTB JobQueue to avoid weakref crash
    app = (
        Application.builder()
        .token(bot_token)
        .job_queue(None)
        .build()
    )

    app.add_error_handler(on_error)
    app.add_handler(CommandHandler("blessnow", blessnow))

    async def _shutdown_scheduler(app: Application) -> None:
        sched = app.bot_data.get("apscheduler")
        if sched:
            logger.info("Shutting down APScheduler...")
            sched.shutdown(wait=False)

    app.post_shutdown = _shutdown_scheduler

    async def _post_init(app: Application) -> None:
        await set_bot_info(app)

        # Seed joke rotation from local jokes.json
        try:
            store = get_store()
            store.refresh_inventory()
            store.build_rotation()
            logger.info("Joke rotation ready")
        except Exception as e:
            logger.warning("Could not warm joke rotation store: %s", e)

        sched = AsyncIOScheduler(timezone=os.getenv("TZ", "America/Los_Angeles"))
        sched.start()
        schedule_hourly_420(sched, ritual_call, app=app)
        logger.info("Scheduler armed: %d jobs", len(sched.get_jobs()))
        app.bot_data["apscheduler"] = sched

    app.post_init = _post_init

    logger.info("App built")
    return app


def main() -> int:
    configure_logging()

    logger.info("=" * 60)
    logger.info("Toka 420 Time Bot Starting")
    logger.info("=" * 60)

    load_dotenv(override=True)
    validate_env_permissions()
    validate_config()

    max_retries = int(os.getenv("POLLING_BOOTSTRAP_MAX_RETRIES", "5"))
    base_delay  = float(os.getenv("POLLING_BOOTSTRAP_BASE_DELAY_SECONDS", "2"))

    # Build once outside the retry loop — avoids redundant store warmup on retries
    app = build_app()

    for attempt in range(max_retries + 1):
        logger.info("Starting polling (attempt %d)...", attempt + 1)
        try:
            app.run_polling(drop_pending_updates=True)
            return 0
        except (TimedOut, NetworkError) as e:
            if attempt >= max_retries:
                logger.exception("Polling failed after %d retries: %s", max_retries, e)
                raise

            delay = min(base_delay * (2 ** attempt), 60.0)
            logger.warning(
                "Polling error (%s). Retrying in %.1fs (%d/%d)",
                e.__class__.__name__, delay, attempt + 1, max_retries,
            )
            time.sleep(delay)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        raise SystemExit(1)
