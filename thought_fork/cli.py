# Copyright 2026
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Thought Fork — Command-line interface.

Usage:
    thought-fork "Should I use microservices?" --forks 3
    thought-fork "Review this architecture" --forks 4 --static
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from dotenv import load_dotenv


# Fork colors for terminal output (ANSI escape codes)
FORK_COLORS = [
    "\033[94m",   # Blue
    "\033[93m",   # Yellow/Amber
    "\033[91m",   # Red
    "\033[92m",   # Green
    "\033[95m",   # Magenta
    "\033[96m",   # Cyan
    "\033[90m",   # Gray
]
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def _print_banner() -> None:
    """Print the Thought Fork banner."""
    print()
    print(f"{BOLD}🔀 Thought Fork — Branch your AI's reasoning{RESET}")
    print()


def _print_fork_result(fork_detail: dict, color: str) -> None:
    """Print a single fork's output with styled header."""
    print()
    print(f"{color}{BOLD}{'═' * 60}{RESET}")
    print(f"{color}{BOLD}  Fork {fork_detail['id']} — {fork_detail['stance']}{RESET}")
    print(f"{color}{BOLD}{'═' * 60}{RESET}")
    print()
    print(fork_detail["output"])
    print()


def _print_synthesis(synthesis_text: str) -> None:
    """Print the synthesis output with styled header."""
    print()
    print(f"{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  ✦ Synthesis (Convergence){RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")
    print()
    print(synthesis_text)
    print()


def _print_summary(fork_details: list[dict], token_usage: dict, duration_ms: int) -> None:
    """Print token usage summary."""
    print(f"{BOLD}📊 Token Usage Summary{RESET}")
    print(f"┌──────┬──────────────────────────────┬────────┬──────────┐")
    print(f"│ Fork │ Stance                       │ Tokens │ Duration │")
    print(f"├──────┼──────────────────────────────┼────────┼──────────┤")

    for detail in fork_details:
        duration_s = detail["duration_ms"] / 1000
        stance = detail["stance"][:28]
        print(
            f"│ {detail['id']:<4} │ {stance:<28} │ {detail['token_count']:>6} │ {duration_s:>6.1f}s  │"
        )

    print(f"├──────┼──────────────────────────────┼────────┼──────────┤")
    total_s = duration_ms / 1000
    print(
        f"│ {'ALL':<4} │ {'TOTAL':<28} │ {token_usage['total']:>6} │ {total_s:>6.1f}s  │"
    )
    print(f"└──────┴──────────────────────────────┴────────┴──────────┘")
    print()


async def _run(prompt: str, fork_count: int, use_dynamic: bool) -> None:
    """Execute a Thought Fork session."""
    from thought_fork import ForkConfig, synthesize

    config = ForkConfig(use_dynamic_stances=use_dynamic)

    _print_banner()
    print(f"{BOLD}Prompt:{RESET} {prompt}")
    print(f"{DIM}Forks: {fork_count} | Dynamic stances: {'on' if use_dynamic else 'off'}{RESET}")
    print()
    print("⏳ Forking...")

    result = await synthesize(prompt, fork_count=fork_count, config=config)

    # Print each fork
    for i, detail in enumerate(result.fork_details):
        color = FORK_COLORS[i % len(FORK_COLORS)]
        _print_fork_result(detail, color)

    # Print synthesis
    _print_synthesis(result.synthesis)

    # Print summary
    _print_summary(result.fork_details, result.token_usage, result.duration_ms)

    print(
        f"{DIM}Forks ran in parallel — wall-clock time is the slowest fork, "
        f"not the sum.{RESET}"
    )
    print()


def main() -> None:
    """CLI entry point for Thought Fork."""
    # Ensure UTF-8 output on Windows terminals
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="thought-fork",
        description="🔀 Thought Fork — Branch your AI's reasoning like Git branches.",
        epilog="Example: thought-fork \"Should I use microservices?\" --forks 3",
    )
    parser.add_argument(
        "prompt",
        help="The question or problem to fork into parallel reasoning paths.",
    )
    parser.add_argument(
        "--forks", "-n",
        type=int,
        default=3,
        help="Number of parallel forks to spawn (default: 3).",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Use static built-in stances instead of AI-selected dynamic stances.",
    )

    args = parser.parse_args()

    try:
        asyncio.run(_run(args.prompt, args.forks, use_dynamic=not args.static))
    except KeyboardInterrupt:
        print(f"\n{DIM}Cancelled.{RESET}")
        sys.exit(0)
    except ValueError as e:
        print(f"\n❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
