# Copyright 2026 Thought Fork Contributors — Apache 2.0 License

"""
Thought Fork — Decision Making Example

Forks "Should I quit my job and go freelance?" using the simple
synthesize() API with default stances.

Usage:
    python examples/decision_making.py
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

    prompt = "Should I quit my job and go freelance?"

    print(f"\n{BOLD}🔀 Thought Fork — Decision Making{RESET}")
    print(f"{DIM}Prompt: {prompt}{RESET}")
    print(f"{DIM}Using default stances: cautious, creative, critical{RESET}\n")

    # Simple 3-line API
    result = await synthesize(prompt, fork_count=3)

    # Show individual forks
    for stance, output in result.forks.items():
        print(f"\n{BOLD}═══ {stance.title()} Fork ═══{RESET}")
        print(output)

    # Show synthesis
    print(f"\n{BOLD}═══ ✦ Synthesis ═══{RESET}")
    print(result.synthesis)

    # Stats
    print(f"\n{DIM}Tokens: {result.token_usage}")
    print(f"Total time: {result.duration_ms / 1000:.1f}s{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
