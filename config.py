"""
Configuration management for the Telegram Goal Planning Bot.
Uses pydantic-settings to load and validate environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = Field(
        ...,
        description="Telegram Bot API token from @BotFather"
    )

    # Supabase Configuration
    SUPABASE_URL: str = Field(
        ...,
        description="Supabase project URL"
    )
    SUPABASE_KEY: str = Field(
        ...,
        description="Supabase anon/service key"
    )

    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = Field(
        ...,
        description="OpenRouter API key for AI integration"
    )
    OPENROUTER_MODEL: str = Field(
        default="xiaomi/mimo-v2-flash:free",
        description="OpenRouter model to use for AI operations"
    )

    # Application Settings
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    DEFAULT_TIMEZONE: str = Field(
        default="UTC",
        description="Default timezone for users"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
