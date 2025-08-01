"""Database models for WeeklyRoulette bot."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ChannelConfig:
    """Configuration for a Slack channel's weekly roulette."""

    channel_id: str
    day: str  # monday, tuesday, wednesday, thursday, friday, saturday, sunday
    time: str  # "HH:MM" format (24-hour)
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ChannelConfig":
        """Create ChannelConfig from database row."""
        return cls(
            channel_id=row["channel_id"],
            day=row["day"],
            time=row["time"],
            enabled=bool(row["enabled"]),
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "channel_id": self.channel_id,
            "day": self.day,
            "time": self.time,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Valid days for scheduling
VALID_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# Day display names for UI
DAY_DISPLAY_NAMES = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
}
