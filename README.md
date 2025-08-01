# WeeklyRoulette Slack Bot 🎲

A Slack bot that automatically selects a random person from channel members on a weekly schedule.

## Features

- **Automated Weekly Selection**: Randomly picks one person from all channel members
- **Flexible Scheduling**: Choose any day of the week and time
- **Easy Configuration**: Simple slash commands and interactive UI
- **Test Mode**: Try it out before scheduling
- **Socket Mode**: No need for public webhooks or HTTPS endpoints

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Slack workspace with admin permissions

### 2. Installation

```bash
# Clone and enter the project
git clone <your-repo>
cd weeklyroulette-bot

# Install dependencies
poetry install

# Copy environment template
cp .env.example .env
```

### 3. Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app "From scratch"
3. Configure the following:

#### OAuth & Permissions (Bot Token Scopes):
```
app_mentions:read
channels:read
users:read
chat:write
commands
```

#### Socket Mode:
- Enable Socket Mode ✅
- Generate App-Level Token with `connections:write` scope

#### Event Subscriptions:
```
app_mention
```

#### Slash Commands:
```
Command: /weeklyroulette
Description: Configure and manage weekly roulette
```

### 4. Environment Setup

Edit `.env` file with your Slack tokens:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
DATABASE_URL=sqlite:///weeklyroulette.db
```

### 5. Run the Bot

```bash
# Initialize database
make setup-db

# Start the bot
make run
```

## Usage

### 1. Invite the Bot
Mention the bot in any channel: `@WeeklyRoulette`

### 2. Configure Schedule
```
/weeklyroulette config
```
Choose your preferred day and time using the interactive modal.

### 3. Test It
```
/weeklyroulette test
```
Run a test selection to make sure everything works.

### 4. Check Status
```
/weeklyroulette status
```
View current configuration and schedule.

## Development

### Available Commands

```bash
make help              # Show all available commands
make dev-install       # Install dev dependencies + pre-commit hooks
make run              # Start the bot
make test             # Run tests
make format           # Format code with black + isort
make lint             # Run linting (flake8 + mypy)
make check            # Run all checks (format + lint + test)
```

### Project Structure

```
src/weeklyroulette_bot/
├── main.py                 # Entry point
├── bot.py                  # Slack app configuration
├── database/
│   ├── models.py          # Data models
│   └── connection.py      # Database operations
├── services/
│   ├── roulette.py        # Roulette logic
│   └── scheduler.py       # Automated scheduling
└── handlers/
    ├── events.py          # Event handlers (@mentions)
    ├── commands.py        # Slash command handlers
    └── actions.py         # Interactive component handlers
```

### Tech Stack

- **Python 3.11+** with type hints
- **Slack Bolt SDK** for official Slack integration
- **SQLite** for simple, reliable data storage
- **Socket Mode** for easy development (no webhooks needed)
- **Schedule** library for automated execution
- **Poetry** for modern dependency management

## Commands Reference

| Command | Description |
|---------|-------------|
| `/weeklyroulette config` | Configure weekly schedule |
| `/weeklyroulette test` | Run test selection |
| `/weeklyroulette status` | Show current settings |
| `/weeklyroulette help` | Show help message |

## Configuration Options

- **Days**: Monday through Sunday
- **Times**: 8:00 AM to 6:30 PM (30-minute intervals)
- **Status**: Enable/disable automatic selection
- **Per-channel**: Each channel has independent configuration

## Troubleshooting

### Bot doesn't respond
- Check if bot token is valid
- Ensure Socket Mode is enabled
- Verify bot has required permissions

### "No active members" error
- Bot needs `users:read` and `channels:read` permissions
- Make sure channel has non-bot members

### Scheduled roulette not working
- Check if configuration is enabled
- Verify scheduler is running (check logs)
- Confirm time zone settings

## 📝 License

MIT License - feel free to modify and use for your team!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make check` to ensure code quality
5. Submit a pull request

---

Made with ❤️ for teams who want fair, automated selection processes!
