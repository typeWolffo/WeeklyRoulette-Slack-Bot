"""Slack bot configuration and setup for WeeklyRoulette."""

import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from database.connection import init_database
from services.roulette import RouletteService
from services.scheduler import SchedulerService


class WeeklyRouletteBot:
    """Main bot class that configures and manages the Slack application."""

    def __init__(self):
        """Initialize the WeeklyRoulette bot."""
        # Initialize database
        init_database()

        # Create Slack app with Socket Mode
        self.app = App(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
            process_before_response=True,  # Enable async processing
        )

        # Initialize services
        self.roulette_service = RouletteService(self.app)
        self.scheduler_service = SchedulerService(self.roulette_service)

        # Register handlers
        self._register_handlers()

        # Start scheduler
        self.scheduler_service.start()

        print("🤖 WeeklyRoulette bot initialized successfully!")

    def _register_handlers(self) -> None:
        """Register all Slack event handlers."""
        # Import handlers here to avoid circular imports
        from handlers.actions import register_action_handlers
        from handlers.commands import register_command_handlers
        from handlers.events import register_event_handlers

        # Register all handlers
        register_event_handlers(self.app, self.roulette_service)
        register_command_handlers(
            self.app, self.roulette_service, self.scheduler_service
        )
        register_action_handlers(
            self.app, self.roulette_service, self.scheduler_service
        )

    def start(self) -> None:
        """Start the bot using Socket Mode."""
        if not os.environ.get("SLACK_APP_TOKEN"):
            raise ValueError(
                "SLACK_APP_TOKEN environment variable is required for Socket Mode"
            )

        handler = SocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
        print("🚀 Starting WeeklyRoulette bot in Socket Mode...")
        handler.start()

    def stop(self) -> None:
        """Stop the bot and cleanup resources."""
        print("🛑 Stopping WeeklyRoulette bot...")
        self.scheduler_service.stop()
        print("✅ Bot stopped successfully")


def create_bot() -> WeeklyRouletteBot:
    """Factory function to create and configure the bot."""
    return WeeklyRouletteBot()
