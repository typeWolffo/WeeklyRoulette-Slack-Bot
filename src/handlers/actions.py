"""Interactive action handlers for WeeklyRoulette bot."""

from slack_bolt import Ack, App
from slack_sdk import WebClient

from database.models import DAY_DISPLAY_NAMES, ChannelConfig
from services.roulette import RouletteService
from services.scheduler import SchedulerService


def register_action_handlers(
    app: App, roulette_service: RouletteService, scheduler_service: SchedulerService
) -> None:
    """Register all interactive action handlers."""

    @app.view("config_modal")
    def handle_config_modal_submission(ack: Ack, body: dict, client: WebClient) -> None:
        """Handle configuration modal submission."""
        ack()

        try:
            # Extract form data
            view = body["view"]
            channel_id = view["private_metadata"]
            values = view["state"]["values"]

            # Get selected values
            day_block = next(iter(values.values()))
            day = day_block["day_select"]["selected_option"]["value"]

            time_block = list(values.values())[1]
            time = time_block["time_select"]["selected_option"]["value"]

            enabled_block = list(values.values())[2]
            enabled = (
                enabled_block["enabled_select"]["selected_option"]["value"] == "true"
            )

            # Create and save configuration
            config = ChannelConfig(
                channel_id=channel_id, day=day, time=time, enabled=enabled
            )

            roulette_service.db.save_channel_config(config)

            # Update scheduler
            scheduler_service.force_update_schedules()

            # Send confirmation message
            day_name = DAY_DISPLAY_NAMES[day]
            status_emoji = "✅" if enabled else "⏸️"

            confirmation_message = (
                f"{status_emoji} **Configuration saved!**\n\n"
                f"📅 Day: {day_name}\n"
                f"🕒 Time: {time}\n"
            )

            if enabled:
                confirmation_message += (
                    f"🎯 First automatic selection will happen on "
                    f"next {day_name.lower()} at {time}.\n\n"
                )
            else:
                confirmation_message += (
                    "⚠️ Automatic selection is disabled. "
                    "Use `/weeklyroulette config` again to enable it."
                )

            client.chat_postMessage(channel=channel_id, text=confirmation_message)

            print(
                f"✅ Configuration saved for channel {channel_id}: "
                f"{day} at {time} (enabled: {enabled})"
            )

        except Exception as e:
            print(f"❌ Error handling config modal submission: {e}")

            # Send error message
            try:
                client.chat_postMessage(
                    channel=channel_id,
                    text="❌ An error occurred while saving configuration. Please try again.",
                )
            except Exception:
                pass

    @app.action("day_select")
    def handle_day_select(ack: Ack) -> None:
        """Handle day selection in config modal."""
        ack()

    @app.action("time_select")
    def handle_time_select(ack: Ack) -> None:
        """Handle time selection in config modal."""
        ack()

    @app.action("enabled_select")
    def handle_enabled_select(ack: Ack) -> None:
        """Handle enabled/disabled selection in config modal."""
        ack()

    print("✅ Action handlers registered")
