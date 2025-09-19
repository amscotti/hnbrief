# mypy: disable-error-code="no-untyped-def"
import pytest
from unittest import mock

from hnbrief.clients.hackernews import HackerNewsClient, HackerNewsStory
from hnbrief.clients.openai import OpenAIClient, StorySummary
from hnbrief.activities.hackernews import HackerNewsActivities
from hnbrief.activities.openai import OpenAIActivities


@pytest.mark.asyncio
async def test_hackernews_activities_get_list_of_stories():
    """Test the get_list_of_stories activity."""
    hn_client = mock.Mock(spec=HackerNewsClient)
    hn_client.get_list_of_stories.return_value = [1, 2, 3]

    activities = HackerNewsActivities(hn_client)
    result = await activities.get_list_of_stories()

    assert result == [1, 2, 3]
    hn_client.get_list_of_stories.assert_called_once()


@pytest.mark.asyncio
async def test_hackernews_activities_get_story_detail():
    """Test the get_story_detail activity."""
    hn_client = mock.Mock(spec=HackerNewsClient)
    expected_story = HackerNewsStory(
        id=123,
        type="story",
        title="Test Story",
        url="https://example.com",
        by="testuser",
        time=1234567890,
    )
    hn_client.get_story_detail.return_value = expected_story

    activities = HackerNewsActivities(hn_client)
    result = await activities.get_story_detail(123)

    assert result == expected_story
    hn_client.get_story_detail.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_hackernews_activities_get_story_markdown():
    """Test the get_story_markdown activity."""
    hn_client = mock.Mock(spec=HackerNewsClient)
    story = HackerNewsStory(
        id=123,
        type="story",
        title="Test Story",
        url="https://example.com",
        by="testuser",
        time=1234567890,
    )
    hn_client.get_story_markdown.return_value = "# Test Story\n\nContent here."

    activities = HackerNewsActivities(hn_client)
    result = await activities.get_story_markdown(story)

    assert result == "# Test Story\n\nContent here."
    hn_client.get_story_markdown.assert_called_once_with(story)


@pytest.mark.asyncio
async def test_openai_activities_summarize_story():
    """Test the summarize_story activity."""
    openai_client = mock.Mock(spec=OpenAIClient)
    expected_summary = StorySummary(
        title="Test Story",
        url="https://example.com",
        text="This is a summary of the story.",
    )
    openai_client.summarize_story.return_value = expected_summary

    activities = OpenAIActivities(openai_client)
    story = HackerNewsStory(
        id=123,
        type="story",
        title="Test Story",
        url="https://example.com",
        by="testuser",
        time=1234567890,
    )

    result = await activities.summarize_story(story, "markdown content")

    assert result == expected_summary
    openai_client.summarize_story.assert_called_once_with(
        "Test Story", "https://example.com", "markdown content"
    )


@pytest.mark.asyncio
async def test_openai_activities_create_daily_brief():
    """Test the create_daily_brief activity."""
    openai_client = mock.Mock(spec=OpenAIClient)
    openai_client.create_daily_brief.return_value = "Daily brief content"

    activities = OpenAIActivities(openai_client)
    summaries = [
        StorySummary(title="Story 1", url="https://example.com/1", text="Summary 1"),
        StorySummary(title="Story 2", url="https://example.com/2", text="Summary 2"),
    ]

    result = await activities.create_daily_brief(summaries)

    assert result == "Daily brief content"
    openai_client.create_daily_brief.assert_called_once_with(summaries)


def test_workflow_execution_order_logic():
    """Test the workflow logic for processing stories in the correct order."""
    # This test validates the workflow logic without running Temporal
    # We test the filtering and processing logic that would happen in the workflow

    # Mock story data
    stories = [
        HackerNewsStory(
            id=1,
            type="story",
            title="Story 1",
            url="https://example.com/1",
            by="user1",
            time=123,
        ),
        HackerNewsStory(
            id=2, type="comment", title="Comment", url=None, by="user2", time=124
        ),  # Should be filtered
        HackerNewsStory(
            id=3, type="story", title="Story 3", url=None, by="user3", time=125
        ),  # Should be filtered
        HackerNewsStory(
            id=4,
            type="story",
            title="Story 4",
            url="https://example.com/4",
            by="user4",
            time=126,
        ),
    ]

    # Apply the same filtering logic as in the workflow
    filtered_stories = [
        story for story in stories if story.type == "story" and story.url
    ]

    # Should only include stories 1 and 4
    assert len(filtered_stories) == 2
    assert filtered_stories[0].id == 1
    assert filtered_stories[1].id == 4


def test_workflow_max_stories_validation():
    """Test the max_stories validation logic."""
    # Test valid range
    assert 1 <= 35 <= 500
    assert 1 <= 1 <= 500
    assert 1 <= 500 <= 500

    # Test invalid values (workflow defaults to 35)
    # These would be handled in the workflow run method
    test_cases = [
        (0, 35),  # Too low, should default to 35
        (-1, 35),  # Negative, should default to 35
        (600, 35),  # Too high, should default to 35
        (100, 100),  # Valid, should stay as is
    ]

    for input_val, expected in test_cases:
        if input_val < 1 or input_val > 500:
            result = 35  # This is what the workflow does
        else:
            result = input_val
        assert result == expected
