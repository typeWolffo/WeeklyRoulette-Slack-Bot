"""Roulette service for selecting random users from Slack channels."""

import random
from typing import List, Optional

from slack_bolt import App
from slack_sdk.errors import SlackApiError

from database.connection import get_database
from services.anthropic_service import AnthropicService


class RouletteService:
    """Service for handling weekly roulette logic."""

    def __init__(self, app: App):
        """Initialize roulette service with Slack app instance."""
        self.app = app
        self.db = get_database()
        self.anthropic_service = AnthropicService()

    async def get_channel_members(self, channel_id: str) -> List[dict]:
        """Get all members of a channel."""
        try:
            # Get channel members
            response = self.app.client.conversations_members(channel=channel_id)
            member_ids = response["members"]

            # Filter out bots and get user info
            active_members = []
            for user_id in member_ids:
                try:
                    user_info = self.app.client.users_info(user=user_id)
                    user = user_info["user"]

                    # Skip bots, deactivated users, and deleted users
                    if (
                        not user.get("is_bot", False)
                        and not user.get("deleted", False)
                        and user.get("id") != "USLACKBOT"
                    ):
                        active_members.append(
                            {
                                "id": user["id"],
                                "name": user.get("display_name")
                                or user.get("real_name")
                                or user.get("name"),
                                "real_name": user.get("real_name", ""),
                                "title": user.get("profile", {}).get("title", "Developer"),
                            }
                        )
                except SlackApiError:
                    # Skip users we can't fetch info for
                    continue

            return active_members

        except SlackApiError as e:
            print(f"Error fetching channel members for {channel_id}: {e}")
            return []

    def select_random_member(self, members: List[dict], last_selected_user_id: Optional[str] = None) -> Optional[dict]:
        """Select a random member from the list, avoiding consecutive selections."""
        if not members:
            return None

        # Filter out the last selected user if there are other options
        available_members = members.copy()
        if last_selected_user_id and len(members) > 1:
            available_members = [m for m in members if m['id'] != last_selected_user_id]
            if available_members:
                print(f"🙅 Excluding last selected user {last_selected_user_id} from selection")
            else:
                # If filtering leaves no one, use all members (shouldn't happen with >1 member)
                available_members = members
                print(f"⚠️ Warning: Could not exclude last user, using all members")

        # Shuffle the list to ensure better randomness
        shuffled_members = available_members.copy()
        random.shuffle(shuffled_members)

        # Add some debug info
        print(f"🎲 Selecting from {len(shuffled_members)} members: {[m['name'] for m in shuffled_members]}")
        if last_selected_user_id:
            print(f"📅 Last selected user ID: {last_selected_user_id}")

        selected = random.choice(shuffled_members)
        print(f"🎯 Selected: {selected['name']} (ID: {selected['id']})")

        return selected

    async def run_roulette(self, channel_id: str, test_mode: bool = False) -> dict:
        """Run roulette for a specific channel."""
        # Get channel config
        config = self.db.get_channel_config(channel_id)
        if not config and not test_mode:
            return {
                "success": False,
                "error": "Channel is not configured. Use `/weeklyroulette config`",
            }

        # Get channel members
        members = await self.get_channel_members(channel_id)
        if not members:
            return {
                "success": False,
                "error": "No active channel members found",
            }

        # Select random member (avoiding consecutive selections)
        last_selected_user_id = config.last_selected_user if config else None
        selected_member = self.select_random_member(members, last_selected_user_id)
        if not selected_member:
            return {"success": False, "error": "Failed to select member"}

        # Generate AI kudo rain message for non-test selections
        kudo_message = None
        if not test_mode and self.anthropic_service.is_configured():
            try:
                # Use Slack mention format: <@USER_ID>
                slack_handle = f"<@{selected_member['id']}>"
                user_title = selected_member.get('title', 'Developer')
                kudo_message = await self.anthropic_service.generate_kudo_rain(
                    slack_handle, user_title
                )
                print(f"💼 Selected {selected_member['name']} (title: {user_title})")

            except Exception as e:
                print(f"⚠️ Failed to generate kudo rain: {e}")

        # Create result message
        member_count = len(members)
        message_prefix = (
            "🎲 **Test Roulette**" if test_mode else "🎯 **Weekly Roulette**"
        )

        if kudo_message and not test_mode:
            # Use AI-generated kudo rain message
            message = (
                f"✨ {kudo_message}"
            )
        else:
            # Use standard message
            message = (
                f"{message_prefix}"
                f"🎉 Selected person: <@{selected_member['id']}>\n"
            )

        if not test_mode and config:
            message += (
                f"\n📅 Next selection: {config.day.title()} at {config.time}"
            )

            # Update last selected user in database (only for real selections, not tests)
            try:
                self.db.update_last_selected_user(channel_id, selected_member['id'])
            except Exception as e:
                print(f"⚠️ Failed to update last selected user: {e}")

        return {
            "success": True,
            "selected_member": selected_member,
            "total_members": member_count,
            "message": message,
            "is_test": test_mode,
        }

    async def send_roulette_message(
        self, channel_id: str, test_mode: bool = False
    ) -> dict:
        """Run roulette and send message to channel."""
        result = await self.run_roulette(channel_id, test_mode)

        if result["success"]:
            try:
                # Send message to channel
                self.app.client.chat_postMessage(
                    channel=channel_id,
                    text=result["message"],
                    unfurl_links=False,
                    unfurl_media=False,
                )
                return result
            except SlackApiError as e:
                return {
                    "success": False,
                    "error": f"Error sending message: {e.response['error']}",
                }

        return result

    def get_channel_status(self, channel_id: str) -> dict:
        """Get status information for a channel."""
        config = self.db.get_channel_config(channel_id)

        if not config:
            return {
                "configured": False,
                "message": (
                    "❌ Channel is not configured yet.\n"
                    "Use `/weeklyroulette config` to set up schedule."
                ),
            }

        status_emoji = "✅" if config.enabled else "⏸️"
        status_text = "enabled" if config.enabled else "disabled"

        from database.models import DAY_DISPLAY_NAMES

        day_name = DAY_DISPLAY_NAMES.get(config.day, config.day.title())

        message = (
            f"{status_emoji} **WeeklyRoulette Status**\n\n"
            f"📅 Day: {day_name}\n"
            f"🕒 Time: {config.time}\n"
            f"🔄 Status: {status_text}\n\n"
            f"💡 Use `/weeklyroulette config` to change settings"
        )

        return {
            "configured": True,
            "enabled": config.enabled,
            "config": config,
            "message": message,
        }
