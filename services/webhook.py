"""
TradingView HOB alert webhook receiver — local / Docker deployment.

Used when running the bot on your own server. Set WEBHOOK_ENABLED=true in .env.

For Vercel (HTTPS, no port), use the Next.js API route instead:
  web/pages/api/webhook/tradingview.ts  →  https://<app>.vercel.app/api/webhook/tradingview
"""

import datetime as dt
import hmac
import json
import logging
import os
import sqlite3

from aiohttp import web

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "jokes.db")


# ── Schema ────────────────────────────────────────────────────────────────────

def ensure_alerts_schema(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create the alerts table if it doesn't exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at     TEXT    NOT NULL,
                ticker          TEXT,
                exchange        TEXT,
                timeframe       TEXT,
                action          TEXT,
                price           TEXT,
                raw_body        TEXT    NOT NULL,
                telegram_sent   INTEGER NOT NULL DEFAULT 0,
                telegram_error  TEXT
            )
            """
        )
        conn.commit()


# ── DB logging ────────────────────────────────────────────────────────────────

def _log_alert(
    db_path: str,
    received_at: str,
    ticker: str | None,
    exchange: str | None,
    timeframe: str | None,
    action: str | None,
    price: str | None,
    raw_body: str,
    telegram_sent: bool,
    telegram_error: str | None,
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO alerts
                (received_at, ticker, exchange, timeframe, action, price,
                 raw_body, telegram_sent, telegram_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                received_at,
                ticker,
                exchange,
                timeframe,
                action,
                price,
                raw_body[:4000],  # cap raw body at 4 KB
                1 if telegram_sent else 0,
                telegram_error,
            ),
        )
        conn.commit()
        return cur.lastrowid


# ── Payload parsing ───────────────────────────────────────────────────────────

def _parse_payload(raw_body: str, content_type: str) -> dict:
    """Parse JSON or plain-text TradingView alert body into a normalised dict."""
    if "application/json" in content_type:
        try:
            data = json.loads(raw_body)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Plain-text fallback — the whole body is the alert message
    return {"message": raw_body.strip()}


# ── Telegram message formatting ───────────────────────────────────────────────

def _format_telegram_message(payload: dict, received_at: str) -> str:
    """Build a human-readable HOB alert for Telegram (MarkdownV2-safe)."""
    action = (payload.get("action") or "").upper()
    ticker = payload.get("ticker") or payload.get("symbol") or ""
    exchange = payload.get("exchange") or ""
    timeframe = payload.get("timeframe") or payload.get("interval") or ""
    price_raw = payload.get("price") or payload.get("close") or ""
    message = payload.get("message") or ""

    if action in ("BUY", "LONG"):
        action_emoji = "🟢"
    elif action in ("SELL", "SHORT"):
        action_emoji = "🔴"
    else:
        action_emoji = "🔵"

    lines = ["📊 *TradingView Alert — HOB Signal*", ""]

    if action and ticker:
        head = f"{action_emoji} *{action}*  `{ticker}`"
        if timeframe:
            head += f"  ·  {timeframe}"
        if exchange:
            head += f"  ·  {exchange}"
        lines.append(head)
    elif ticker:
        lines.append(f"`{ticker}`" + (f"  ·  {exchange}" if exchange else ""))

    if price_raw:
        try:
            price_fmt = f"${float(price_raw):,.4f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            price_fmt = str(price_raw)
        lines.append(f"💰 Price: {price_fmt}")

    if message and message not in (ticker, action):
        lines.append(f"_{message}_")

    lines.append("")
    lines.append(f"🕐 `{received_at[:19]} UTC`")

    if ticker:
        tag = "#" + ticker.replace("/", "").replace("-", "").replace(":", "")
        hashtags = [tag]
        if action:
            hashtags.append(f"#{action.title()}")
        lines.append(" ".join(hashtags))

    return "\n".join(lines)


# ── Authentication ────────────────────────────────────────────────────────────

def _verify_secret(request: web.Request, secret: str) -> bool:
    """Constant-time check of Authorization: Bearer <secret> or X-Webhook-Secret."""
    if not secret:
        return True  # no secret configured → open
    token_bytes = secret.encode()
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        provided = auth[len("Bearer "):]
        return hmac.compare_digest(provided.encode(), token_bytes)
    x_secret = request.headers.get("X-Webhook-Secret", "")
    if x_secret:
        return hmac.compare_digest(x_secret.encode(), token_bytes)
    return False


# ── aiohttp app ───────────────────────────────────────────────────────────────

def make_webhook_app(
    bot,
    chat_id: str,
    db_path: str,
    secret: str,
) -> web.Application:
    ensure_alerts_schema(db_path)

    async def handle_tradingview(request: web.Request) -> web.Response:
        if not _verify_secret(request, secret):
            logger.warning("Webhook: unauthorised request from %s", request.remote)
            return web.Response(status=401, text="Unauthorized")

        try:
            raw_body = await request.text()
        except Exception as exc:
            logger.warning("Webhook: failed to read body: %s", exc)
            return web.Response(status=400, text="Bad Request")

        if not raw_body.strip():
            return web.Response(status=400, text="Empty body")

        content_type = request.headers.get("Content-Type", "")
        received_at = dt.datetime.now(dt.timezone.utc).isoformat()
        payload = _parse_payload(raw_body, content_type)

        ticker = payload.get("ticker") or payload.get("symbol") or None
        exchange = payload.get("exchange") or None
        timeframe = payload.get("timeframe") or payload.get("interval") or None
        action = ((payload.get("action") or "").upper()) or None
        price = str(payload.get("price") or payload.get("close") or "").strip() or None

        text = _format_telegram_message(payload, received_at)

        telegram_sent = False
        telegram_error = None
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            telegram_sent = True
            logger.info(
                "Webhook: alert sent ticker=%s action=%s price=%s",
                ticker, action, price,
            )
        except Exception as exc:
            telegram_error = str(exc)
            logger.error("Webhook: Telegram send failed: %s", exc)

        try:
            alert_id = _log_alert(
                db_path=db_path,
                received_at=received_at,
                ticker=ticker,
                exchange=exchange,
                timeframe=timeframe,
                action=action,
                price=price,
                raw_body=raw_body,
                telegram_sent=telegram_sent,
                telegram_error=telegram_error,
            )
            logger.info("Webhook: alert logged id=%d", alert_id)
        except Exception as exc:
            logger.error("Webhook: DB log failed: %s", exc)

        status = 200 if telegram_sent else 202
        return web.Response(status=status, text="OK" if telegram_sent else "Accepted")

    app = web.Application()
    app.router.add_post("/webhook/tradingview", handle_tradingview)
    return app


async def start_webhook_server(
    bot,
    chat_id: str,
    db_path: str = DEFAULT_DB_PATH,
    secret: str = "",
    port: int = 8080,
) -> web.AppRunner:
    """Start the webhook HTTP server; return the runner so the caller can stop it."""
    web_app = make_webhook_app(bot, chat_id, db_path, secret)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(
        "Webhook server listening on 0.0.0.0:%d → POST /webhook/tradingview", port
    )
    return runner
