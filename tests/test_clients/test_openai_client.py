# mypy: disable-error-code="no-untyped-def"
import pytest
from unittest import mock

from hnbrief.clients.openai import OpenAIClient, StorySummary


@pytest.mark.asyncio
async def test_summarize_story_success():
    """Test successful story summarization."""
    # Mock the config to avoid validation errors
    with mock.patch("hnbrief.clients.openai.get_openai_config") as mock_config:
        mock_config.return_value.summarize_model = "test-model"
        client = OpenAIClient("https://api.example.com", "test-key")

        # Mock the OpenAI client
        mock_response = mock.Mock()
        mock_response.choices = [mock.Mock()]
        mock_response.choices[0].message.content = "This is a summary of the story."

        # Mock the POML function
        with mock.patch("hnbrief.clients.openai.poml.poml") as mock_poml:
            with mock.patch.object(
                client.client.chat.completions,
                "create",
                mock.AsyncMock(return_value=mock_response),
            ):
                mock_poml.return_value = {
                    "messages": [{"role": "user", "content": "test"}]
                }

                result = await client.summarize_story(
                    "Test Title", "https://example.com", "# Markdown content"
                )

                assert isinstance(result, StorySummary)
                assert result.title == "Test Title"
                assert result.url == "https://example.com"
                assert result.text == "This is a summary of the story."

                # Verify POML was called with correct context
                mock_poml.assert_called_once()
                call_args = mock_poml.call_args
                assert call_args[1]["context"]["title"] == "Test Title"
                assert call_args[1]["context"]["markdown"] == "# Markdown content"


@pytest.mark.asyncio
async def test_summarize_story_empty_markdown():
    """Test summarization when markdown is empty."""
    # Mock the config to avoid validation errors
    with mock.patch("hnbrief.clients.openai.get_openai_config") as mock_config:
        mock_config.return_value.summarize_model = "test-model"
        client = OpenAIClient("https://api.example.com", "test-key")

        result = await client.summarize_story("Test Title", "https://example.com", "")

        assert isinstance(result, StorySummary)
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.text == ""


@pytest.mark.asyncio
async def test_summarize_story_openai_error():
    """Test handling of OpenAI API errors."""
    # Mock the config to avoid validation errors
    with mock.patch("hnbrief.clients.openai.get_openai_config") as mock_config:
        mock_config.return_value.summarize_model = "test-model"
        client = OpenAIClient("https://api.example.com", "test-key")

        # Mock the POML function
        with mock.patch("hnbrief.clients.openai.poml.poml") as mock_poml:
            with mock.patch.object(
                client.client.chat.completions,
                "create",
                mock.AsyncMock(side_effect=Exception("API Error")),
            ):
                mock_poml.return_value = {
                    "messages": [{"role": "user", "content": "test"}]
                }

                result = await client.summarize_story(
                    "Test Title", "https://example.com", "# Content"
                )

                assert isinstance(result, StorySummary)
                assert result.title == "Test Title"
                assert result.url == "https://example.com"
                assert result.text == ""  # Should return empty text on error


@pytest.mark.asyncio
async def test_create_daily_brief_success():
    """Test successful daily brief creation."""
    # Mock the config to avoid validation errors
    with mock.patch("hnbrief.clients.openai.get_openai_config") as mock_config:
        mock_config.return_value.daily_brief_model = "test-model"
        client = OpenAIClient("https://api.example.com", "test-key")

        summaries = [
            StorySummary(
                title="Story 1", url="https://example.com/1", text="Summary 1"
            ),
            StorySummary(
                title="Story 2", url="https://example.com/2", text="Summary 2"
            ),
        ]

        # Mock the OpenAI client
        mock_response = mock.Mock()
        mock_response.choices = [mock.Mock()]
        mock_response.choices[0].message.content = "Daily brief content here."

        # Mock the POML function
        with mock.patch("hnbrief.clients.openai.poml.poml") as mock_poml:
            with mock.patch.object(
                client.client.chat.completions,
                "create",
                mock.AsyncMock(return_value=mock_response),
            ):
                mock_poml.return_value = {
                    "messages": [{"role": "user", "content": "test"}]
                }

                result = await client.create_daily_brief(summaries)

                assert result == "Daily brief content here."

                # Verify POML was called with correct context
                mock_poml.assert_called_once()
                call_args = mock_poml.call_args
                assert len(call_args[1]["context"]["summaries"]) == 2
                assert "current_date" in call_args[1]["context"]


@pytest.mark.asyncio
async def test_create_daily_brief_empty_summaries():
    """Test daily brief creation with no summaries."""
    # Mock the config to avoid validation errors
    with mock.patch("hnbrief.clients.openai.get_openai_config") as mock_config:
        mock_config.return_value.daily_brief_model = "test-model"
        client = OpenAIClient("https://api.example.com", "test-key")

        result = await client.create_daily_brief([])

        assert result == "No stories to summarize."


@pytest.mark.asyncio
async def test_create_daily_brief_openai_error():
    """Test handling of OpenAI API errors in daily brief creation."""
    # Mock the config to avoid validation errors
    with mock.patch("hnbrief.clients.openai.get_openai_config") as mock_config:
        mock_config.return_value.daily_brief_model = "test-model"
        client = OpenAIClient("https://api.example.com", "test-key")

        summaries = [
            StorySummary(
                title="Story 1", url="https://example.com/1", text="Summary 1"
            ),
        ]

        # Mock the POML function
        with mock.patch("hnbrief.clients.openai.poml.poml") as mock_poml:
            with mock.patch.object(
                client.client.chat.completions,
                "create",
                mock.AsyncMock(side_effect=Exception("API Error")),
            ):
                mock_poml.return_value = {
                    "messages": [{"role": "user", "content": "test"}]
                }

                result = await client.create_daily_brief(summaries)

                assert result == "Failed to generate daily brief."
