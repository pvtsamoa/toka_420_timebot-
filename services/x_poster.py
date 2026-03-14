import hashlib
import logging
import os
import threading
import time

import requests

logger = logging.getLogger(__name__)
dispatch_logger = logging.getLogger("toka.dispatch")

_TRUE_VALUES = {"1", "true", "yes", "on"}
_DUPLICATE_WINDOW_SECONDS = 90
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_STATE_LOCK = threading.Lock()
_LAST_POST = {"fingerprint": None, "ts": 0.0}


def _is_enabled() -> bool:
    return (os.getenv("X_POST_ENABLED", "false").strip().lower() in _TRUE_VALUES)


def format_for_x(text: str, max_chars: int = 280) -> str:
    """Normalize whitespace and trim to X's max tweet length."""
    normalized = " ".join((text or "").split())
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 3:
        return normalized[:max_chars]
    return normalized[: max_chars - 3].rstrip() + "..."


def _fingerprint(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _has_recent_duplicate(message: str) -> bool:
    fingerprint = _fingerprint(message)
    now = time.time()

    with _STATE_LOCK:
        previous_fingerprint = _LAST_POST["fingerprint"]
        previous_ts = _LAST_POST["ts"]

        if previous_fingerprint == fingerprint and (now - previous_ts) < _DUPLICATE_WINDOW_SECONDS:
            return True

    return False


def _mark_post_success(message: str) -> None:
    with _STATE_LOCK:
        _LAST_POST["fingerprint"] = _fingerprint(message)
        _LAST_POST["ts"] = time.time()


def _x_credentials():
    keys = {
        "X_API_KEY": os.getenv("X_API_KEY", "").strip(),
        "X_API_SECRET": os.getenv("X_API_SECRET", "").strip(),
        "X_ACCESS_TOKEN": os.getenv("X_ACCESS_TOKEN", "").strip(),
        "X_ACCESS_TOKEN_SECRET": os.getenv("X_ACCESS_TOKEN_SECRET", "").strip(),
    }
    missing = [name for name, value in keys.items() if not value]
    return keys, missing


def post_mirror(text: str) -> bool:
    """Mirror a Telegram ritual post to X in best-effort mode."""
    if not _is_enabled():
        return False

    message = format_for_x(text)
    if not message:
        logger.warning("X mirror skipped: empty message")
        dispatch_logger.warning("dispatch_failure side=x reason=empty_message")
        return False

    if _has_recent_duplicate(message):
        logger.info("X mirror skipped: duplicate message within %ss", _DUPLICATE_WINDOW_SECONDS)
        dispatch_logger.warning("dispatch_failure side=x reason=duplicate_window")
        return False

    keys, missing = _x_credentials()
    if missing:
        logger.warning("X mirror enabled but missing credentials: %s", ", ".join(missing))
        dispatch_logger.warning("dispatch_failure side=x reason=missing_credentials missing=%s", ",".join(missing))
        return False

    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        logger.error("X mirror requires requests-oauthlib. Install dependencies from requirements.txt")
        dispatch_logger.error("dispatch_failure side=x reason=missing_dependency dependency=requests-oauthlib")
        return False

    auth = OAuth1(
        keys["X_API_KEY"],
        keys["X_API_SECRET"],
        keys["X_ACCESS_TOKEN"],
        keys["X_ACCESS_TOKEN_SECRET"],
    )

    # Time-sensitive default: one immediate attempt at 4:20, then move on.
    max_attempts = max(1, int(os.getenv("X_POST_MAX_ATTEMPTS", "1")))
    retry_delay = max(0.2, float(os.getenv("X_POST_RETRY_DELAY_SECONDS", "1.5")))

    last_status = None
    last_body = ""

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                "https://api.twitter.com/2/tweets",
                json={"text": message},
                auth=auth,
                timeout=12,
                headers={"User-Agent": "toka-420-timebot"},
            )
        except requests.RequestException as exc:
            if attempt < max_attempts:
                wait = retry_delay * attempt
                logger.warning(
                    "X mirror network/API error on attempt %d/%d: %s. Retrying in %.1fs",
                    attempt,
                    max_attempts,
                    exc,
                    wait,
                )
                time.sleep(wait)
                continue

            logger.warning("X mirror failed due to network/API error: %s", exc)
            dispatch_logger.warning("dispatch_failure side=x reason=network_error error=%s", exc)
            return False

        if response.status_code in (200, 201):
            _mark_post_success(message)
            logger.info("Ritual mirrored to X successfully")
            return True

        body = (response.text or "").replace("\n", " ").strip()
        if len(body) > 240:
            body = body[:240] + "..."

        last_status = response.status_code
        last_body = body

        if response.status_code in _RETRYABLE_STATUS and attempt < max_attempts:
            wait = retry_delay * attempt
            logger.warning(
                "X mirror transient failure status=%s on attempt %d/%d. Retrying in %.1fs",
                response.status_code,
                attempt,
                max_attempts,
                wait,
            )
            time.sleep(wait)
            continue

        logger.warning("X mirror failed status=%s body=%s", response.status_code, body)
        dispatch_logger.warning(
            "dispatch_failure side=x reason=http_status status=%s body=%s",
            response.status_code,
            body,
        )
        return False

    logger.warning("X mirror failed after retries status=%s body=%s", last_status, last_body)
    dispatch_logger.warning(
        "dispatch_failure side=x reason=retry_exhausted status=%s body=%s",
        last_status,
        last_body,
    )
    return False
