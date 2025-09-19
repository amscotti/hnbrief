# mypy: disable-error-code="no-untyped-def"
from hnbrief.clients.hackernews import HackerNewsClient, HackerNewsStory


def test_hackernews_client_initialization():
    """Test that HackerNewsClient can be initialized."""
    client = HackerNewsClient()
    assert client is not None


def test_story_model_validation():
    """Test that HackerNewsStory model validates correctly."""
    story = HackerNewsStory(
        id=123,
        type="story",
        title="Test Story",
        url="https://example.com",
        by="testuser",
        time=1234567890,
        score=100,
        descendants=10,
        kids=[124, 125],
    )

    assert story.id == 123
    assert story.type == "story"
    assert story.title == "Test Story"
    assert story.url == "https://example.com"
    assert story.by == "testuser"
    assert story.score == 100
    assert story.descendants == 10
    assert story.kids == [124, 125]


def test_story_model_optional_fields():
    """Test that optional fields work correctly."""
    story = HackerNewsStory(
        id=456,
        type="story",
        title="Minimal Story",
        by="user",
        time=1234567890,
    )

    assert story.id == 456
    assert story.url is None
    assert story.score is None
    assert story.descendants is None
    assert story.kids == []


def test_story_model_filtering_logic():
    """Test the story filtering logic that would be used in workflows."""
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
