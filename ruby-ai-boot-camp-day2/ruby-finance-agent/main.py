"""Run the finance research orchestrator from the command line."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from agents import Runner

AGENTS_DIR = Path(__file__).resolve().parent / "agents"
sys.path.insert(0, str(AGENTS_DIR))
from orchestrator import orchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an evidence-based company or earnings report."
    )
    parser.add_argument(
        "request",
        nargs="?",
        default="Prepare an earnings report for AAPL.",
        help="The company research request to send to the orchestrator.",
    )
    return parser.parse_args()


async def run(request: str) -> str:
    result = await Runner.run(orchestrator, request)
    return result.final_output


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    args = parse_args()
    print(asyncio.run(run(args.request)))


if __name__ == "__main__":
    main()