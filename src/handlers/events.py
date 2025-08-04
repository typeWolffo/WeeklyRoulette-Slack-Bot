"""Event handlers for WeeklyRoulette bot."""

from slack_bolt import App
from slack_bolt.context.say import Say
from slack_sdk import WebClient

from services.roulette import RouletteService


def register_event_handlers(app: App, roulette_service: RouletteService) -> None:
    """Register all event handlers."""

    @app.event("app_mention")
    def handle_app_mention(event: dict, say: Say, client: WebClient) -> None:
        """Handle when the bot is mentioned in a channel."""
        channel_id = event["channel"]
        user_id = event["user"]

        welcome_message = (
            f"👋 Hello <@{user_id}>!\n\n"
            "🎲 I'm **WeeklyRoulette** - a bot for weekly random selection of channel members!\n\n"
            "**How to get started:**\n"
            "• Use `/weeklyroulette config` to set up schedule\n"
            "• Choose day and time for automatic selection\n"
            "• Done! I'll automatically pick someone each week\n\n"
            "**Available commands:**\n"
            "• `/weeklyroulette config` - configure schedule\n"
            "• `/weeklyroulette status` - check current settings\n\n"
            "📝 *I need permissions to read channel members and send messages.*"
        )

        say(text=welcome_message, channel=channel_id)

        print(f"👋 App mentioned in channel {channel_id} by user {user_id}")

    @app.event("member_joined_channel")
    def handle_member_joined(event: dict, client: WebClient) -> None:
        """Handle when a new member joins a channel with the bot."""
        channel_id = event["channel"]
        user_id = event["user"]

        print(f"👤 New member {user_id} joined channel {channel_id}")

    @app.event("member_left_channel")
    def handle_member_left(event: dict, client: WebClient) -> None:
        """Handle when a member leaves a channel with the bot."""
        channel_id = event["channel"]
        user_id = event["user"]

        print(f"👋 Member {user_id} left channel {channel_id}")

    print("✅ Event handlers registered")
