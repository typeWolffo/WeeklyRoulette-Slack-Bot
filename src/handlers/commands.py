"""Slash command handlers for WeeklyRoulette bot."""

import asyncio

from slack_bolt import Ack, App
from slack_bolt.context.respond import Respond
from slack_sdk import WebClient

from database.models import DAY_DISPLAY_NAMES, VALID_DAYS
from services.roulette import RouletteService
from services.scheduler import SchedulerService


def register_command_handlers(
    app: App, roulette_service: RouletteService, scheduler_service: SchedulerService
) -> None:
    """Register all slash command handlers."""

    @app.command("/weeklyroulette")
    def handle_weeklyroulette_command(
        ack: Ack, command: dict, client: WebClient, respond: Respond
    ) -> None:
        """Handle /weeklyroulette slash command."""
        ack()

        text = command.get("text", "").strip()
        channel_id = command["channel_id"]

        if not text or text == "help":
            help_message = (
                "🎲 **WeeklyRoulette - Help**\n\n"
                "**Available commands:**\n"
                "• `/weeklyroulette config` - configure selection schedule\n"
                "• `/weeklyroulette status` - check current settings\n"
                "• `/weeklyroulette help` - show this help\n\n"
                "**How it works:**\n"
                "1. Configure day and time for selection\n"
                "2. Bot automatically picks a random person from channel\n"
                "3. Selection happens every week at the set time\n\n"
            )
            respond(text=help_message)
            return

        if text == "config":
            _show_config_modal(client, command["trigger_id"], channel_id)
            return

        if text == "test":
            result = asyncio.run(
                roulette_service.send_roulette_message(channel_id, test_mode=True)
            )

            if result["success"]:
                respond(
                    text=f"✅ Test completed successfully!\n\n{result['message']}\n\n"
                    f"💡 *This was just a test. Regular selection will happen automatically according to schedule.*"
                )
            else:
                respond(text=f"❌ Test failed: {result['error']}")
            return

        if text == "status":
            status = roulette_service.get_channel_status(channel_id)
            respond(text=status["message"])
            return

        respond(
            text="❓ Unknown command. Use `/weeklyroulette help` to see available options."
        )

    def _show_config_modal(client: WebClient, trigger_id: str, channel_id: str) -> None:
        """Show configuration modal dialog."""

        current_config = roulette_service.db.get_channel_config(channel_id)

        day_options = []
        for day in VALID_DAYS:
            day_options.append(
                {
                    "text": {"type": "plain_text", "text": DAY_DISPLAY_NAMES[day]},
                    "value": day,
                }
            )

        time_options = []
        for hour in range(9, 17):  # 9:00 to 16:55 (96 options, under Slack's 100 limit)
            for minute in range(0, 60, 5):  # 5-minute intervals
                time_str = f"{hour:02d}:{minute:02d}"
                display_time = f"{hour:02d}:{minute:02d}"
                time_options.append(
                    {
                        "text": {"type": "plain_text", "text": display_time},
                        "value": time_str,
                    }
                )

        default_day = current_config.day if current_config else "friday"
        default_time = current_config.time if current_config else "15:00"
        default_enabled = current_config.enabled if current_config else True

        modal_view = {
            "type": "modal",
            "callback_id": "config_modal",
            "title": {"type": "plain_text", "text": "Configuration"},
            "submit": {"type": "plain_text", "text": "Save"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "private_metadata": channel_id,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🎲 *Configure weekly selection schedule*",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "📅 *Choose day of week:*"},
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Select day"},
                        "action_id": "day_select",
                        "initial_option": {
                            "text": {
                                "type": "plain_text",
                                "text": DAY_DISPLAY_NAMES[default_day],
                            },
                            "value": default_day,
                        },
                        "options": day_options,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🕒 *Choose time (Polish time):*",
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select time",
                        },
                        "action_id": "time_select",
                        "initial_option": {
                            "text": {"type": "plain_text", "text": default_time},
                            "value": default_time,
                        },
                        "options": time_options,
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🔄 *Status:*"},
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Select status"},
                        "action_id": "enabled_select",
                        "initial_option": {
                            "text": {
                                "type": "plain_text",
                                "text": "Enabled" if default_enabled else "Disabled",
                            },
                            "value": "true" if default_enabled else "false",
                        },
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "Enabled"},
                                "value": "true",
                            },
                            {
                                "text": {"type": "plain_text", "text": "Disabled"},
                                "value": "false",
                            },
                        ],
                    },
                },
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "💡 *Bot will automatically select one person from the channel at the chosen time*",
                        }
                    ],
                },
            ],
        }

        try:
            client.views_open(trigger_id=trigger_id, view=modal_view)
        except Exception as e:
            print(f"Error opening config modal: {e}")

    print("✅ Command handlers registered")
