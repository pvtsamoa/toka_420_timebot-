"""
Persistence service for bot settings and state.

Saves bot configuration to JSON files in the data/ directory.
"""
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BotPersistence:
    """Handle loading and saving bot state to JSON files."""

    def __init__(self, data_dir: str):
        """
        Initialize persistence handler.

        Args:
            data_dir: Directory to store persistence files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.data_dir / "bot_settings.json"
        self._cache = {}

    def load_settings(self) -> Dict[str, Any]:
        """
        Load bot settings from JSON file.

        Returns:
            Dictionary of settings, or defaults if file doesn't exist
        """
        defaults = {
            "420_mode": "both",
            "last_ritual_tzs": [],
            "ritual_count": 0,
        }

        if not self.settings_file.exists():
            logger.info("No settings file found, using defaults")
            self._cache = defaults.copy()
            return defaults

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                logger.info("Loaded settings from %s", self.settings_file)
                self._cache = settings
                return settings
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in settings file: %s", e)
            return defaults
        except Exception as e:
            logger.exception("Error loading settings: %s", e)
            return defaults

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save bot settings to JSON file.

        Args:
            settings: Dictionary of settings to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update cache
            self._cache.update(settings)

            # Write to file with pretty formatting
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)

            logger.info("Settings saved to %s", self.settings_file)
            return True
        except Exception as e:
            logger.exception("Error saving settings: %s", e)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a single setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a single setting value and save.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            True if successful, False otherwise
        """
        self._cache[key] = value
        return self.save_settings({key: value})

    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric setting.

        Args:
            key: Setting key
            amount: Amount to increment by

        Returns:
            New value
        """
        current = self._cache.get(key, 0)
        new_value = current + amount
        self.set(key, new_value)
        return new_value

    def get_stats(self) -> Dict[str, Any]:
        """
        Get bot statistics.

        Returns:
            Dictionary of stats
        """
        return {
            "420_mode": self._cache.get("420_mode", "both"),
            "ritual_count": self._cache.get("ritual_count", 0),
            "last_ritual_tzs": self._cache.get("last_ritual_tzs", []),
        }


# Global persistence instance (initialized in app.py)
_persistence: Optional[BotPersistence] = None


def init_persistence(data_dir: str) -> BotPersistence:
    """
    Initialize the global persistence instance.

    Args:
        data_dir: Directory to store persistence files

    Returns:
        BotPersistence instance
    """
    global _persistence
    _persistence = BotPersistence(data_dir)
    return _persistence


def get_persistence() -> Optional[BotPersistence]:
    """
    Get the global persistence instance.

    Returns:
        BotPersistence instance or None if not initialized
    """
    return _persistence
