"""Command-line entry point for educational equity research."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .agents.orchestrator import run_research_workflow


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the educational equity research workflow.",
        epilog=(
            "Pass a research request as arguments, or run without one "
            "to be prompted."
        ),
    )
    parser.add_argument(
        "request",
        nargs="*",
        help="Company/ticker and research question, for example: AAPL outlook",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the async workflow and return a process code."""
    args = _parse_args(argv)
    request = " ".join(args.request).strip()
    if not request:
        try:
            request = input(
                "Research request (company/ticker and question): "
            ).strip()
        except EOFError:
            print("No research request provided.", file=sys.stderr)
            return 2
        except KeyboardInterrupt:
            print("Research workflow interrupted.", file=sys.stderr)
            return 130
    if not request:
        print("A non-empty research request is required.", file=sys.stderr)
        return 2

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print(
            "OPENAI_API_KEY is not set. Configure it in the environment "
            "and retry.",
            file=sys.stderr,
        )
        return 2

    try:
        result = asyncio.run(run_research_workflow(request))
    except KeyboardInterrupt:
        print("Research workflow interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        # Provider exceptions may include request details; report the class.
        print(
            f"Research workflow failed ({type(exc).__name__}).", file=sys.stderr
        )
        return 1

    print(result)
    return 1 if result.startswith("[Research workflow incomplete:") else 0


if __name__ == "__main__":
    raise SystemExit(main())
