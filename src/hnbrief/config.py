"""Configuration management for hnbrief application."""

import sys
from typing import Optional

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings


class TemporalConfig(BaseSettings):
    """Temporal-specific configuration for worker and CLI."""

    temporal_server_url: str = Field(default="localhost:7233")


class OpenAIConfig(BaseSettings):
    """OpenAI-specific configuration for workflow activities."""

    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1", validation_alias="OPENAI_BASE_URL"
    )

    openai_api_key: str = Field(default=..., validation_alias="OPENROUTER_API_KEY")

    summarize_model: str = Field(
        default="x-ai/grok-4-fast:free", validation_alias="SUMMARIZE_MODEL"
    )

    daily_brief_model: str = Field(
        default="x-ai/grok-4-fast:free", validation_alias="DAILY_BRIEF_MODEL"
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: Optional[str]) -> str:
        if v is None or not v.strip():
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Please set it with your OpenAI/OpenRouter API key:\n"
                "export OPENROUTER_API_KEY=your_api_key_here"
            )
        return v.strip()


class HackerNewsConfig(BaseSettings):
    """HackerNews-specific configuration for workflow."""

    max_stories: int = Field(default=35, validation_alias="MAX_STORIES", ge=1, le=500)


def get_temporal_config() -> TemporalConfig:
    """Get Temporal configuration."""
    return TemporalConfig()


def get_openai_config() -> OpenAIConfig:
    """Get OpenAI configuration."""
    try:
        return OpenAIConfig()
    except ValidationError as e:
        for error in e.errors():
            if "msg" in error:
                msg = error["msg"]
                if msg.startswith("Value error, "):
                    msg = msg[13:]
                print(msg)
                sys.exit(1)
        # Fallback
        print(str(e))
        sys.exit(1)


def get_hackernews_config() -> HackerNewsConfig:
    """Get HackerNews configuration."""
    try:
        return HackerNewsConfig()
    except ValidationError:
        print("MAX_STORIES must be between 1 and 500 due to API limits.")
        sys.exit(1)
