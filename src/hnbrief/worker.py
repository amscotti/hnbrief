import asyncio
import logging
import signal
import sys

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from hnbrief.activities.hackernews import HackerNewsActivities
from hnbrief.activities.openai import OpenAIActivities
from hnbrief.clients.hackernews import HackerNewsClient
from hnbrief.clients.openai import OpenAIClient
from hnbrief.config import get_temporal_config, get_openai_config
from hnbrief.workflows.hackernews import HackerNewsDailyBrief

# Configure logging
logger = logging.getLogger(__name__)


async def main() -> None:
    # Create shutdown event for graceful shutdown
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def shutdown_handler(signum: int) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Initiating shutdown...")
        shutdown_event.set()

    # Register async-safe signal handlers
    try:
        loop.add_signal_handler(signal.SIGINT, shutdown_handler, signal.SIGINT)
        loop.add_signal_handler(signal.SIGTERM, shutdown_handler, signal.SIGTERM)
    except (OSError, ValueError) as e:
        # Handle platforms that don't support these signals (e.g., Windows)
        logger.warning(f"Signal handling not fully supported: {e}")

    try:
        # Connect to Temporal server
        temporal_config = get_temporal_config()
        temporal_client = await Client.connect(
            temporal_config.temporal_server_url,
            data_converter=pydantic_data_converter,
        )

        # Instantiate clients and activity classes
        hn_client = HackerNewsClient()
        hn_activities = HackerNewsActivities(hn_client)

        openai_config = get_openai_config()
        openai_client = OpenAIClient(
            openai_config.openai_base_url, openai_config.openai_api_key
        )
        openai_activities = OpenAIActivities(openai_client)

        # Create and run worker
        worker = Worker(
            temporal_client,
            task_queue="hacker-news-task-queue",
            workflows=[HackerNewsDailyBrief],
            activities=[
                hn_activities.get_list_of_stories,
                hn_activities.get_story_detail,
                hn_activities.get_story_markdown,
                openai_activities.summarize_story,
                openai_activities.create_daily_brief,
            ],
        )

        print("Worker started, polling task queue...")
        print("Press Ctrl+C to stop gracefully")

        # Run worker task
        worker_task = asyncio.create_task(worker.run())

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Graceful shutdown
        logger.info("Shutting down worker...")
        await worker.shutdown()

        # Cancel and clean up worker task
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        if "Connection refused" in str(e):
            print(
                "Unable to connect to Temporal server. Please ensure the Temporal server is running."
            )
            temporal_config = get_temporal_config()
            print(f"Expected server at: {temporal_config.temporal_server_url}")
        else:
            logger.error(f"Error during worker execution: {e}")
        sys.exit(1)
    finally:
        logger.info("Worker shutdown complete.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
