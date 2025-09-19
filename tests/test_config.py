import pytest

from hnbrief.config import (
    get_temporal_config,
    get_openai_config,
    get_hackernews_config,
    TemporalConfig,
    OpenAIConfig,
    HackerNewsConfig,
)


def test_get_temporal_config_defaults() -> None:
    """Test Temporal config loads with defaults."""
    config = get_temporal_config()
    assert isinstance(config, TemporalConfig)
    assert config.temporal_server_url == "localhost:7233"


def test_get_temporal_config_with_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Temporal config overrides with environment variable."""
    monkeypatch.setenv("TEMPORAL_SERVER_URL", "custom:9999")
    config = get_temporal_config()
    assert config.temporal_server_url == "custom:9999"


def test_get_openai_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test OpenAI config loads with required env var."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "valid-key")
    monkeypatch.setenv("SUMMARIZE_MODEL", "custom-model")
    config = get_openai_config()
    assert isinstance(config, OpenAIConfig)
    assert config.openai_api_key == "valid-key"
    assert config.summarize_model == "custom-model"
    assert config.openai_base_url == "https://openrouter.ai/api/v1"  # Default


@pytest.mark.parametrize(
    "api_key, expected_error",
    [
        (None, "Field required"),
        ("", "OPENROUTER_API_KEY environment variable is required."),
    ],
)
def test_get_openai_config_validation_errors(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str | None,
    expected_error: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test OpenAI config raises errors for invalid/missing API key."""
    if api_key is not None:
        monkeypatch.setenv("OPENROUTER_API_KEY", api_key)
    else:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit):
        get_openai_config()

    captured = capsys.readouterr()
    assert expected_error in captured.out


def test_get_hackernews_config_defaults() -> None:
    """Test HackerNews config loads with defaults."""
    config = get_hackernews_config()
    assert isinstance(config, HackerNewsConfig)
    assert config.max_stories == 35


def test_get_hackernews_config_with_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test HackerNews config overrides with environment variable."""
    monkeypatch.setenv("MAX_STORIES", "50")
    config = get_hackernews_config()
    assert config.max_stories == 50


@pytest.mark.parametrize(
    "max_stories, should_raise",
    [
        (0, True),
        (501, True),
        (35, False),
    ],
)
def test_get_hackernews_config_validation(
    monkeypatch: pytest.MonkeyPatch, max_stories: int, should_raise: bool
) -> None:
    """Test HackerNews config validation for max_stories range."""
    monkeypatch.setenv("MAX_STORIES", str(max_stories))

    if should_raise:
        with pytest.raises(SystemExit):
            get_hackernews_config()
    else:
        config = get_hackernews_config()
        assert config.max_stories == max_stories
