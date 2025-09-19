import aiohttp
import html2text
import logging
from typing import Optional
from pydantic import BaseModel, Field, RootModel


# Constants
STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL_BASE = "https://hacker-news.firebaseio.com/v0/item"


class StoryIds(RootModel[list[int]]):
    """Pydantic model for list of story IDs."""

    root: list[int]


class HackerNewsStory(BaseModel):
    """Pydantic model for HackerNews story data."""

    id: int
    type: str
    title: str
    url: Optional[str] = None
    text: Optional[str] = None
    by: str
    time: int
    score: Optional[int] = None
    descendants: Optional[int] = None
    kids: Optional[list[int]] = Field(default_factory=lambda: [])


class HackerNewsClient:
    """Client for interacting with HackerNews API."""

    async def get_list_of_stories(self) -> list[int]:
        """Get the list of top story IDs from HackerNews."""
        async with aiohttp.ClientSession() as session:
            async with session.get(STORIES_URL) as response:
                response.raise_for_status()
                all_ids = await response.json()
                story_ids = StoryIds(root=all_ids)
                return story_ids.root

    async def get_story_detail(self, story_id: int) -> HackerNewsStory:
        """Get detailed information for a specific story."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ITEM_URL_BASE}/{story_id}.json") as response:
                response.raise_for_status()
                data = await response.json()
                return HackerNewsStory.model_validate(data)

    async def get_story_markdown(self, story: HackerNewsStory) -> str:
        """Fetch story content and convert to markdown."""
        if not story.url:
            return ""

        logging.info(f"Fetching markdown for story: {story.title}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(story.url, headers=headers) as response:
                    response.raise_for_status()
                    html = await response.text()
                    return html2text.html2text(html)
            except Exception as e:
                logging.error(f"Failed to fetch markdown for {story.title}: {e}")
                return ""
