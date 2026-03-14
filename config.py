from dataclasses import dataclass, field
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class Settings:
    # All defaults use default_factory so they are evaluated at call time,
    # not at class-definition time — ensures .env values are picked up.
    TELEGRAM_BOT_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    TELEGRAM_SCOPE: str = field(default_factory=lambda: os.getenv("TELEGRAM_SCOPE", "all"))

    # Split CHAT_IDS by comma to list of strings.
    CHAT_IDS: list[str] = field(
        default_factory=lambda: os.getenv("CHAT_IDS", "").split(",") if os.getenv("CHAT_IDS") else []
    )

    WEEDCOIN_TOKEN: str = field(default_factory=lambda: os.getenv("WEEDCOIN_TOKEN", "Weedcoin"))

    # File-relative paths — safe regardless of launch directory
    BASE_DIR: str = field(default_factory=lambda: _HERE)
    DATA_DIR: str = field(default_factory=lambda: os.path.join(_HERE, "data"))
    MEDIA_DIR: str = field(default_factory=lambda: os.path.join(_HERE, "media"))


def get_settings() -> Settings:
    """Read environment-backed settings at call time."""
    return Settings()
