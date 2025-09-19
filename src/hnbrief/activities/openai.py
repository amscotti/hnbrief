from temporalio import activity

from hnbrief.clients.hackernews import HackerNewsStory
from hnbrief.clients.openai import OpenAIClient, StorySummary


class OpenAIActivities:
    """Activities for interacting with OpenAI API."""

    def __init__(self, client: OpenAIClient):
        self.client = client

    @activity.defn
    async def summarize_story(
        self, story: HackerNewsStory, markdown: str
    ) -> StorySummary:
        """Summarize a story using OpenAI."""
        return await self.client.summarize_story(story.title, story.url, markdown)

    @activity.defn
    async def create_daily_brief(self, summaries: list[StorySummary]) -> str:
        """Create a daily brief from story summaries."""
        return await self.client.create_daily_brief(summaries)
