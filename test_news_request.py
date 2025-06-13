#!/usr/bin/env python3
"""
Quick test for the trending news request
"""
import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
)
logger = logging.getLogger("news_test")

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import needed modules
from app.agent.router import AgentRouter
from app.config import get_config
from app.memory import Memory


async def test_news_request():
    """Test the specific request: build a webpage with trending news"""

    memory = Memory()
    agent = AgentRouter()  # Initialize with default parameters

    prompt = "build a webpage with trending news today"
    logger.info(f"Testing prompt: '{prompt}'")

    try:
        response = await agent.route(prompt)  # Route the query to the appropriate agent

        # Check if there are tool calls
        tool_calls = []

        if isinstance(response, dict):
            if "tool_calls" in response:
                tool_calls = response["tool_calls"]
            elif (
                "content" in response
                and isinstance(response["content"], dict)
                and "tool_calls" in response["content"]
            ):
                tool_calls = response["content"]["tool_calls"]

        if tool_calls:
            logger.info(f"Success! Found {len(tool_calls)} tool calls:")
            for i, call in enumerate(tool_calls):
                logger.info(f"  Tool #{i+1}: {call.get('name', 'unknown')}")
                if "arguments" in call:
                    logger.info(f"    Arguments: {call['arguments']}")
            return True
        else:
            logger.warning("No tool calls found in response")
            return False

    except Exception as e:
        logger.error(f"Error testing news request: {e}")
        return False


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    success = asyncio.run(test_news_request())
    sys.exit(0 if success else 1)
