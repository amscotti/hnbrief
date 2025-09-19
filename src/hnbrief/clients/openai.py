from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import logging
import poml  # type: ignore[import-untyped]
from openai import AsyncOpenAI

from hnbrief.config import get_openai_config, OpenAIConfig


@dataclass
class StorySummary:
    """Data object for a story summary with title and text."""

    title: str
    url: Optional[str]
    text: str


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        # POML template paths
        self.prompts_dir = Path(__file__).parent.parent / "prompts"

        # Get config for model settings
        self.config: OpenAIConfig = get_openai_config()

    async def summarize_story(
        self, title: str, url: Optional[str], markdown: str
    ) -> StorySummary:
        """Summarize a story using OpenAI."""
        if not markdown:
            return StorySummary(title=title, url=url or "", text="")

        try:
            # Use POML template for story summarization
            template_path = self.prompts_dir / "story_summary.poml"
            params = poml.poml(
                str(template_path),
                format="openai_chat",
                context={"title": title, "markdown": markdown},
            )

            response = await self.client.chat.completions.create(
                **params, model=self.config.summarize_model
            )  # pyright: ignore[reportCallIssue]

            summary_text = response.choices[0].message.content or ""
            return StorySummary(title=title, url=url, text=summary_text)
        except Exception as e:
            logging.error(f"Failed to summarize story '{title}': {e}")
            return StorySummary(title=title, url=url, text="")

    async def create_daily_brief(self, summaries: list[StorySummary]) -> str:
        """Create a daily brief from story summaries."""
        if not summaries:
            return "No stories to summarize."

        try:
            # Use POML template for daily brief creation
            template_path = self.prompts_dir / "daily_brief.poml"
            current_date = datetime.now().strftime("%B %d, %Y")
            params = poml.poml(
                str(template_path),
                format="openai_chat",
                context={
                    "summaries": [asdict(summary) for summary in summaries],
                    "current_date": current_date,
                },
            )

            response = await self.client.chat.completions.create(
                **params, model=self.config.daily_brief_model
            )  # pyright: ignore[reportCallIssue]

            return response.choices[0].message.content or ""
        except Exception as e:
            logging.error(f"Failed to generate daily brief: {e}")
            return "Failed to generate daily brief."
