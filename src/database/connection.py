"""Database connection and operations for WeeklyRoulette bot."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from database.models import ChannelConfig


class DatabaseConnection:
    """Manages SQLite database connection and operations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database connection."""
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///weeklyroulette.db")

        self.database_url = database_url
        self._connection: Optional[sqlite3.Connection] = None

    def _get_db_path(self) -> str:
        """Extract database path from DATABASE_URL."""
        if self.database_url.startswith("sqlite:///"):
            # Remove sqlite:/// prefix
            db_path = self.database_url[10:]
            # Create directory if it doesn't exist
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return db_path
        else:
            raise ValueError(f"Unsupported database URL: {self.database_url}")

    def connect(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            db_path = self._get_db_path()
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._create_tables()
        return self._connection

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.connect().cursor()

        # Channel configurations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channel_configs (
                channel_id TEXT PRIMARY KEY,
                day TEXT NOT NULL,
                time TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_selected_user TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # Migration: Add last_selected_user column if it doesn't exist
        try:
            cursor.execute(
                "ALTER TABLE channel_configs ADD COLUMN last_selected_user TEXT"
            )
            print("✅ Added last_selected_user column to existing database")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        self._connection.commit()

    def get_channel_config(self, channel_id: str) -> Optional[ChannelConfig]:
        """Get configuration for a specific channel."""
        cursor = self.connect().cursor()
        cursor.execute(
            "SELECT * FROM channel_configs WHERE channel_id = ?", (channel_id,)
        )
        row = cursor.fetchone()
        return ChannelConfig.from_row(row) if row else None

    def save_channel_config(self, config: ChannelConfig) -> None:
        """Save or update channel configuration."""
        cursor = self.connect().cursor()
        now = datetime.now().isoformat()

        # Check if config exists
        existing = self.get_channel_config(config.channel_id)

        if existing:
            # Update existing config
            cursor.execute(
                """
                UPDATE channel_configs
                SET day = ?, time = ?, enabled = ?, last_selected_user = ?, updated_at = ?
                WHERE channel_id = ?
            """,
                (config.day, config.time, int(config.enabled), config.last_selected_user, now, config.channel_id),
            )
        else:
            # Insert new config
            cursor.execute(
                """
                INSERT INTO channel_configs (channel_id, day, time, enabled, last_selected_user, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    config.channel_id,
                    config.day,
                    config.time,
                    int(config.enabled),
                    config.last_selected_user,
                    now,
                    now,
                ),
            )

        self._connection.commit()

    def get_all_enabled_configs(self) -> List[ChannelConfig]:
        """Get all enabled channel configurations."""
        cursor = self.connect().cursor()
        cursor.execute("SELECT * FROM channel_configs WHERE enabled = 1")
        rows = cursor.fetchall()
        return [ChannelConfig.from_row(row) for row in rows]

    def update_last_selected_user(self, channel_id: str, user_id: str) -> None:
        """Update only the last selected user for a channel."""
        cursor = self.connect().cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE channel_configs
            SET last_selected_user = ?, updated_at = ?
            WHERE channel_id = ?
            """,
            (user_id, now, channel_id)
        )

        self._connection.commit()
        print(f"📝 Updated last selected user for channel {channel_id}: {user_id}")

    def delete_channel_config(self, channel_id: str) -> bool:
        """Delete channel configuration. Returns True if deleted."""
        cursor = self.connect().cursor()
        cursor.execute(
            "DELETE FROM channel_configs WHERE channel_id = ?", (channel_id,)
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global database instance
_db_instance: Optional[DatabaseConnection] = None


def get_database() -> DatabaseConnection:
    """Get global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


def init_database() -> None:
    """Initialize database (create tables)."""
    db = get_database()
    db.connect()  # This will create tables via _create_tables()
    print("✅ Database initialized successfully!")
