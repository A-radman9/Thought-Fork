# Copyright 2026 — Apache 2.0 License

"""
Thought Fork — Code Review Example

Forks a code review using custom stances: security, performance,
maintainability. Demonstrates the advanced API with custom Fork objects.

Usage:
    python examples/code_review.py
"""

import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from thought_fork import Fork, synthesize


CODE_TO_REVIEW = '''
def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    data = json.loads(result.fetchone()["blob"])
    cache[user_id] = data
    return data
'''

PROMPT = f"Review this Python function for issues:\n```python{CODE_TO_REVIEW}```"

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


async def main():
    load_dotenv()

    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Set OPENROUTER_API_KEY in .env")
        sys.exit(1)

    print(f"\n{BOLD}🔀 Thought Fork — Code Review{RESET}")
    print(f"{DIM}Forking with custom stances: security, performance, maintainability{RESET}\n")

    result = await synthesize(
        PROMPT,
        forks=[
            Fork(id="A", stance="security",
                 system_prompt="You are a security auditor. Find vulnerabilities, injection risks, and unsafe patterns."),
            Fork(id="B", stance="performance",
                 system_prompt="You are a performance engineer. Find bottlenecks, memory issues, and inefficiencies."),
            Fork(id="C", stance="maintainability",
                 system_prompt="You are a code quality reviewer. Find complexity risks, readability issues, and maintenance traps."),
        ],
    )

    for detail in result.fork_details:
        print(f"\n{BOLD}═══ Fork {detail['id']} — {detail['stance'].title()} ═══{RESET}")
        print(detail["output"])

    print(f"\n{BOLD}═══ ✦ Synthesis ═══{RESET}")
    print(result.synthesis)

    print(f"\n{DIM}Tokens: {result.token_usage}{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
