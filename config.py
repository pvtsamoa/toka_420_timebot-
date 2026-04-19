from dataclasses import dataclass, field
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class Settings:
    # Evaluated at call time (default_factory) so .env values are always picked up.
    TELEGRAM_BOT_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    WEEDCOIN_TOKEN:     str = field(default_factory=lambda: os.getenv("WEEDCOIN_TOKEN", "weedcoin"))
    SECONDARY_TOKEN:    str = field(default_factory=lambda: os.getenv("SECONDARY_TOKEN", "ethereum"))

    # File-relative paths — safe regardless of launch directory
    BASE_DIR:  str = field(default_factory=lambda: _HERE)
    DATA_DIR:  str = field(default_factory=lambda: os.path.join(_HERE, "data"))
    MEDIA_DIR: str = field(default_factory=lambda: os.path.join(_HERE, "media"))


def get_settings() -> Settings:
    """Read environment-backed settings at call time."""
    return Settings()
