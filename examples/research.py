# Copyright 2026 Thought Fork Contributors — Apache 2.0 License

"""
Thought Fork — Research Example

Forks a technical research question using 4 stances:
cautious, creative, first-principles, pragmatic.

Usage:
    python examples/research.py
"""

import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from thought_fork import synthesize

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


async def main():
    load_dotenv()

    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Set OPENROUTER_API_KEY in .env")
        sys.exit(1)

    prompt = (
        "What are the most promising approaches to reducing LLM hallucinations, "
        "and which ones are likely to work at scale?"
    )

    print(f"\n{BOLD}🔀 Thought Fork — Research{RESET}")
    print(f"{DIM}Prompt: {prompt}{RESET}")
    print(f"{DIM}Using 4 stances: cautious, creative, first-principles, pragmatic{RESET}\n")

    result = await synthesize(
        prompt,
        fork_count=4,
        stances=["cautious", "creative", "first-principles", "pragmatic"],
    )

    for detail in result.fork_details:
        print(f"\n{BOLD}═══ Fork {detail['id']} — {detail['stance'].title()} ═══{RESET}")
        print(detail["output"])

    print(f"\n{BOLD}═══ ✦ Synthesis ═══{RESET}")
    print(result.synthesis)

    print(f"\n{DIM}Tokens: {result.token_usage}")
    print(f"Total time: {result.duration_ms / 1000:.1f}s{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
