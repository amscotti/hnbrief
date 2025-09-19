"""Main entry point for hnbrief package."""

import argparse
import asyncio
import sys
import uuid

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from hnbrief.config import get_hackernews_config, get_temporal_config
from hnbrief.workflows.hackernews import HackerNewsDailyBrief


async def main() -> None:
    """Main entry point that runs the workflow."""
    parser = argparse.ArgumentParser(description="Run HackerNews workflow")
    hackernews_config = get_hackernews_config()
    parser.add_argument(
        "--max-stories",
        type=int,
        default=hackernews_config.max_stories,
        help="Number of stories to process (1-500, defaults to config value)",
    )
    args = parser.parse_args()

    # Connect to local Temporal server
    temporal_config = get_temporal_config()
    server_url = temporal_config.temporal_server_url
    try:
        temporal_client = await Client.connect(
            server_url,
            data_converter=pydantic_data_converter,
        )
    except Exception as e:
        if "Connection refused" in str(e):
            print(
                "Unable to connect to Temporal server. Please ensure the Temporal server is running."
            )
            print(f"Expected server at: {server_url}")
            sys.exit(1)
        else:
            raise

    print("Starting workflow!")
    # Start the workflow
    result = await temporal_client.execute_workflow(
        HackerNewsDailyBrief.run,
        args=[args.max_stories],
        id=f"hacker-news-workflow-{uuid.uuid4().hex}",
        task_queue="hacker-news-task-queue",
    )

    print(f"Workflow result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
