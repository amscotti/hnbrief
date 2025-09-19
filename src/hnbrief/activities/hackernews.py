from temporalio import activity

from hnbrief.clients.hackernews import HackerNewsClient, HackerNewsStory


class HackerNewsActivities:
    """Activities for interacting with HackerNews API."""

    def __init__(self, client: HackerNewsClient):
        self.client = client

    @activity.defn
    async def get_list_of_stories(self) -> list[int]:
        """Get the list of top story IDs from HackerNews."""
        return await self.client.get_list_of_stories()

    @activity.defn
    async def get_story_detail(self, story_id: int) -> HackerNewsStory:
        """Get detailed information for a specific story."""
        return await self.client.get_story_detail(story_id)

    @activity.defn
    async def get_story_markdown(self, story: HackerNewsStory) -> str:
        """Fetch story content and convert to markdown."""
        return await self.client.get_story_markdown(story)
