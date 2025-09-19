import asyncio
from typing import cast

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from hnbrief.clients.hackernews import HackerNewsStory
from hnbrief.clients.openai import StorySummary


@workflow.defn
class HackerNewsDailyBrief:
    async def _process_story(
        self, story: HackerNewsStory, retry_policy: RetryPolicy
    ) -> StorySummary:
        """Process a single story: get markdown then summarize."""
        # Get markdown for this story
        markdown = await workflow.execute_activity(
            "get_story_markdown",
            result_type=str,
            args=(story,),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        # Summarize this story
        summary = cast(
            StorySummary,
            await workflow.execute_activity(
                "summarize_story",
                result_type=StorySummary,
                args=(story, markdown),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            ),
        )

        return summary

    @workflow.run
    async def run(self, max_stories: int) -> str:
        # Validate max_stories
        if max_stories < 1 or max_stories > 500:
            max_stories = 35  # Fallback to default

        retry_policy = RetryPolicy(
            maximum_attempts=5,
            maximum_interval=timedelta(seconds=5),
            non_retryable_error_types=[],
        )

        # Get list of story IDs
        list_of_ids = await workflow.execute_activity(
            "get_list_of_stories",
            result_type=list[int],
            start_to_close_timeout=timedelta(seconds=5),
            retry_policy=retry_policy,
        )

        # Get details for first N stories
        num_stories = min(max_stories, len(list_of_ids))
        story_ids = list_of_ids[:num_stories]

        # Execute activities concurrently for each story detail
        story_futures = []
        for story_id in story_ids:
            future = workflow.execute_activity(
                "get_story_detail",
                result_type=HackerNewsStory,
                args=(story_id,),
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=retry_policy,
            )
            story_futures.append(future)

        # Wait for all story details to complete concurrently
        story_dicts = await asyncio.gather(*story_futures)

        # Convert dictionaries back to HackerNewsStory objects
        stories: list[HackerNewsStory] = [
            HackerNewsStory.model_validate(story_dict) for story_dict in story_dicts
        ]

        # Filter to only include items of type 'story'
        stories = [story for story in stories if story.type == "story" and story.url]

        # Process each story through its pipeline (markdown → summary) concurrently
        story_processing_futures = [
            self._process_story(story, retry_policy) for story in stories
        ]
        summaries = await asyncio.gather(*story_processing_futures)

        # Create daily brief
        brief = cast(
            str,
            await workflow.execute_activity(
                "create_daily_brief",
                result_type=str,
                args=(summaries,),
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy,
            ),
        )

        return brief
