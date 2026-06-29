# Copyright 2026 Ameen Saeed
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
Thought Fork — Basic Demo

This demo forks the question "Should I build a monolith or microservices
for a new SaaS product?" into 3 parallel reasoning paths (cautious,
creative, critical), then synthesizes them into an attributed answer.

Usage:
    python examples/basic_fork.py
"""

import asyncio
import sys
import os
import time

# Add parent directory to path so we can import thought_fork
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

from thought_fork import ForkConfig, ForkManager, SynthesisEngine


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEMO_PROMPT = (
    "Should I build a monolith or microservices for a new SaaS product?"
)

DEMO_STANCES = ["cautious", "creative", "critical"]

# Fork colors for terminal output (ANSI escape codes)
FORK_COLORS = {
    "cautious": "\033[94m",   # Blue
    "creative": "\033[93m",   # Yellow/Amber
    "critical": "\033[91m",   # Red
    "pragmatic": "\033[92m",  # Green
    "first-principles": "\033[95m",  # Magenta
    "optimistic": "\033[96m",  # Cyan
    "contrarian": "\033[90m",  # Gray
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_header():
    """Print the Thought Fork banner."""
    print()
    print(f"{BOLD}🔀 Thought Fork — Branch your AI's reasoning{RESET}")
    print(f"{DIM}   Forking your prompt into {len(DEMO_STANCES)} reasoning paths...{RESET}")
    print()


def print_fork_result(fork):
    """Print a single fork's output with styled header."""
    color = FORK_COLORS.get(fork.stance, "")
    print()
    print(f"{color}{BOLD}{'═' * 60}{RESET}")
    print(f"{color}{BOLD}  Fork {fork.id} — {fork.stance.title()}{RESET}")
    print(f"{color}{BOLD}{'═' * 60}{RESET}")
    print()
    print(fork.output)
    print()


def print_synthesis(synthesis_text):
    """Print the synthesis output with styled header."""
    print()
    print(f"{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  ✦ Synthesis (Convergence){RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")
    print()
    print(synthesis_text)
    print()


def print_summary_table(forks, synthesis_tokens, synthesis_duration_ms):
    """Print token usage summary table."""
    total_fork_tokens = sum(f.token_count for f in forks)
    total_tokens = total_fork_tokens + synthesis_tokens
    total_fork_time = max(f.duration_ms for f in forks)  # Parallel, so max not sum
    total_time = total_fork_time + synthesis_duration_ms

    print(f"{BOLD}📊 Token Usage Summary{RESET}")
    print(f"┌──────┬──────────────────┬────────┬──────────┐")
    print(f"│ Fork │ Stance           │ Tokens │ Duration │")
    print(f"├──────┼──────────────────┼────────┼──────────┤")

    for fork in forks:
        duration_s = fork.duration_ms / 1000
        print(
            f"│ {fork.id:<4} │ {fork.stance:<16} │ {fork.token_count:>6} │ {duration_s:>6.1f}s  │"
        )

    print(f"├──────┼──────────────────┼────────┼──────────┤")
    syn_duration_s = synthesis_duration_ms / 1000
    print(
        f"│ {'SYN':<4} │ {'synthesis':<16} │ {synthesis_tokens:>6} │ {syn_duration_s:>6.1f}s  │"
    )
    print(f"├──────┼──────────────────┼────────┼──────────┤")
    total_s = total_time / 1000
    print(
        f"│ {'ALL':<4} │ {'TOTAL':<16} │ {total_tokens:>6} │ {total_s:>6.1f}s  │"
    )
    print(f"└──────┴──────────────────┴────────┴──────────┘")
    print()
    print(
        f"{DIM}Forks ran in parallel — wall-clock fork time is the slowest fork, "
        f"not the sum.{RESET}"
    )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    """Run the Thought Fork demo."""
    # Load environment variables
    load_dotenv()

    # Verify API key exists
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY not found in .env file.")
        print("   Copy .env.example to .env and add your OpenRouter API key.")
        sys.exit(1)

    # Initialize
    config = ForkConfig()
    manager = ForkManager(config)
    engine = SynthesisEngine(config)

    # Print banner
    print_header()

    # Show the prompt
    print(f"{BOLD}Prompt:{RESET} {DEMO_PROMPT}")
    print()

    # Step 1: Create forks
    forks = await manager.create_forks(DEMO_PROMPT, DEMO_STANCES)

    # Step 2: Run forks in parallel
    print(f"⏳ Running {len(forks)} forks in parallel...")
    overall_start = time.perf_counter()
    forks = await manager.run_parallel(forks, DEMO_PROMPT)
    fork_wall_time = (time.perf_counter() - overall_start) * 1000

    # Report completion
    for fork in forks:
        duration_s = fork.duration_ms / 1000
        color = FORK_COLORS.get(fork.stance, "")
        print(
            f"  {color}✓ Fork {fork.id} ({fork.stance}) "
            f"completed in {duration_s:.1f}s "
            f"[{fork.token_count} tokens]{RESET}"
        )

    # Step 3: Print each fork's output
    for fork in forks:
        print_fork_result(fork)

    # Step 4: Synthesize
    print(f"⏳ Synthesizing {len(forks)} forks into convergence...")
    synthesis_text, synthesis_tokens, synthesis_duration_ms = (
        await engine.synthesize(DEMO_PROMPT, forks)
    )
    syn_s = synthesis_duration_ms / 1000
    print(f"  ✓ Synthesis completed in {syn_s:.1f}s [{synthesis_tokens} tokens]")

    # Step 5: Print synthesis
    print_synthesis(synthesis_text)

    # Step 6: Summary table
    print_summary_table(forks, synthesis_tokens, synthesis_duration_ms)


if __name__ == "__main__":
    asyncio.run(main())
