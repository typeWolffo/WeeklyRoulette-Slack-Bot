"""Main entry point for WeeklyRoulette Slack bot."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

# Import after path manipulation
from weeklyroulette_bot.bot import create_bot  # noqa: E402


def validate_environment() -> None:
    """Validate that all required environment variables are set."""
    required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_SIGNING_SECRET"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  • {var}")
        print("\n💡 Make sure to:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your Slack app credentials")
        print("  3. Enable Socket Mode in your Slack app")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    print("🚀 Starting WeeklyRoulette Slack Bot...")

    # Load environment variables
    load_dotenv()

    # Validate environment
    validate_environment()

    try:
        # Create and start the bot
        bot = create_bot()
        bot.start()

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
