from dataclasses import dataclass, field
import os

@dataclass(frozen=True)
class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_SCOPE: str = os.getenv("TELEGRAM_SCOPE", "all")

    # Split CHAT_IDS by comma â†’ list of strings
    CHAT_IDS: list[str] = field(
        default_factory=lambda: os.getenv("CHAT_IDS", "").split(",") if os.getenv("CHAT_IDS") else []
    )

    WEEDCOIN_TOKEN: str = os.getenv("WEEDCOIN_TOKEN", "Weedcoin")

    BASE_DIR: str = os.getcwd()
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    MEDIA_DIR: str = os.path.join(BASE_DIR, "media")


SETTINGS = Settings()
