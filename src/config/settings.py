"""Application settings and configuration."""

import os


class Settings:
    """Application settings loaded from environment variables."""

    # Slack Configuration
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.getenv("SLACK_APP_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///weeklyroulette.db"
    )

    # Application Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.ENVIRONMENT.lower() == "production"

    @classmethod
    def validate(cls) -> bool:
        """Validate that all required settings are present."""
        required_settings = [
            cls.SLACK_BOT_TOKEN,
            cls.SLACK_APP_TOKEN,
            cls.SLACK_SIGNING_SECRET,
        ]
        return all(setting for setting in required_settings)


# Global settings instance
settings = Settings()
