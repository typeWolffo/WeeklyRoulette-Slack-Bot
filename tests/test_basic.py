"""Basic tests for WeeklyRoulette bot."""

import os
import tempfile
from unittest.mock import patch

from src.database.connection import DatabaseConnection
from src.database.models import VALID_DAYS, ChannelConfig


class TestChannelConfig:
    """Test ChannelConfig model."""

    def test_channel_config_creation(self):
        """Test creating a channel configuration."""
        config = ChannelConfig(
            channel_id="C12345678", day="friday", time="15:00", enabled=True
        )

        assert config.channel_id == "C12345678"
        assert config.day == "friday"
        assert config.time == "15:00"
        assert config.enabled is True

    def test_channel_config_to_dict(self):
        """Test converting config to dictionary."""
        config = ChannelConfig(
            channel_id="C12345678", day="friday", time="15:00", enabled=True
        )

        config_dict = config.to_dict()
        assert config_dict["channel_id"] == "C12345678"
        assert config_dict["day"] == "friday"
        assert config_dict["time"] == "15:00"
        assert config_dict["enabled"] is True

    def test_valid_days_constant(self):
        """Test that all expected days are in VALID_DAYS."""
        expected_days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        assert VALID_DAYS == expected_days


class TestDatabaseConnection:
    """Test database connection and operations."""

    def test_database_creation(self):
        """Test creating a database connection."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_url = f"sqlite:///{tmp_file.name}"
            db = DatabaseConnection(db_url)

            # Test connection creates tables
            conn = db.connect()
            assert conn is not None

            # Verify table exists
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='channel_configs'
            """
            )
            result = cursor.fetchone()
            assert result is not None

            db.close()
            os.unlink(tmp_file.name)

    def test_save_and_get_config(self):
        """Test saving and retrieving channel configuration."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_url = f"sqlite:///{tmp_file.name}"
            db = DatabaseConnection(db_url)

            # Create test config
            config = ChannelConfig(
                channel_id="C12345678", day="friday", time="15:00", enabled=True
            )

            # Save config
            db.save_channel_config(config)

            # Retrieve config
            retrieved_config = db.get_channel_config("C12345678")

            assert retrieved_config is not None
            assert retrieved_config.channel_id == "C12345678"
            assert retrieved_config.day == "friday"
            assert retrieved_config.time == "15:00"
            assert retrieved_config.enabled is True

            db.close()
            os.unlink(tmp_file.name)


class TestBotImport:
    """Test that bot modules can be imported without errors."""

    @patch.dict(
        os.environ,
        {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "test-secret",
        },
    )
    def test_bot_import(self):
        """Test that we can import the bot module."""
        from src.bot import WeeklyRouletteBot

        assert WeeklyRouletteBot is not None

    def test_services_import(self):
        """Test importing services."""
        from src.services import RouletteService, SchedulerService

        assert RouletteService is not None
        assert SchedulerService is not None

    def test_handlers_import(self):
        """Test importing handlers."""
        from src.handlers import actions, commands, events

        assert events is not None
        assert commands is not None
        assert actions is not None
