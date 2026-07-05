# Copyright 2026 Thought Fork Contributors
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
Thought Fork — Branch your AI's reasoning like Git branches.

Thought Fork spawns N parallel reasoning paths ("forks") from a single prompt,
each biased by a different stance, then merges them into a synthesis with
explicit attribution.

Concept and vocabulary by Thought Fork Contributors, June 2026.

Simple usage::

    from thought_fork import synthesize

    result = await synthesize("Should I migrate to microservices?", fork_count=3)
    print(result.synthesis)          # Attributed final answer
    print(result.forks["cautious"])  # Individual fork output
    print(result.token_usage)        # {"forks": ..., "synthesis": ..., "total": ...}

Advanced usage with custom stances::

    from thought_fork import Fork, synthesize

    result = await synthesize(
        "Review this architecture",
        forks=[
            Fork(id="A", stance="security",     system_prompt="Find vulnerabilities"),
            Fork(id="B", stance="performance",  system_prompt="Find bottlenecks"),
            Fork(id="C", stance="maintainability", system_prompt="Find complexity risks"),
        ]
    )
"""

from __future__ import annotations

import time

__version__ = "0.6.2"
__author__ = "Thought Fork Contributors"

from thought_fork.config import BUILT_IN_STANCES, ForkConfig
from thought_fork.fork import Fork, get_stance_prompt
from thought_fork.manager import ForkManager
from thought_fork.message import Message
from thought_fork.result import ForkResult
from thought_fork.stance_selector import SelectedStance, StanceSelector
from thought_fork.synthesis import (
    FORK_OUTPUT_TEMPLATE,
    SYNTHESIS_SYSTEM_PROMPT,
    SYNTHESIS_USER_TEMPLATE,
    SynthesisEngine,
)


async def synthesize(
    prompt: str,
    fork_count: int = 3,
    stances: list[str] | None = None,
    forks: list[Fork] | None = None,
    history: list[Message] | None = None,
    config: ForkConfig | None = None,
) -> ForkResult:
    """Fork a prompt into parallel reasoning paths and synthesize.

    This is the main entry point for the Thought Fork library.
    It wraps ForkManager + SynthesisEngine into a single async call.

    Args:
        prompt: The question or problem to fork.
        fork_count: Number of forks to spawn (ignored if ``forks`` is provided).
        stances: List of stance names. Defaults to the first N built-in stances.
        forks: Advanced — provide pre-built Fork objects with custom system prompts.
        history: Optional list of previous Message objects for multi-turn context.
        config: Optional ForkConfig to override model selection and limits.

    Returns:
        A ForkResult containing the synthesis, individual fork outputs,
        and token usage statistics.
    """
    config = config or ForkConfig()
    manager = ForkManager(config)
    engine = SynthesisEngine(config)

    overall_start = time.perf_counter()

    # Create or use provided forks
    if forks is not None:
        # Advanced: caller provided pre-built Fork objects
        fork_list = forks
    elif stances is not None:
        # Caller specified explicit stance names → use built-ins / custom prompts
        fork_list = manager.create_forks(prompt, stances)
    elif config.use_dynamic_stances:
        # Default: let AI invent the best stances for this prompt
        selector = StanceSelector(config)
        selected = await selector.select(prompt, fork_count, history)
        fork_list = selector.to_forks(selected)
    else:
        # Dynamic stances disabled → use configured default stances
        resolved_stances = list(BUILT_IN_STANCES.keys())[:fork_count]
        fork_list = manager.create_forks(prompt, resolved_stances)

    # Run forks in parallel
    fork_list = await manager.run_parallel(fork_list, prompt, history)

    # Synthesize
    synthesis_text, synthesis_tokens, synthesis_duration = (
        await engine.synthesize(prompt, fork_list, history)
    )

    # Build result
    total_fork_tokens = sum(f.token_count for f in fork_list)
    total_tokens = total_fork_tokens + synthesis_tokens
    overall_duration = int((time.perf_counter() - overall_start) * 1000)

    return ForkResult(
        synthesis=synthesis_text,
        forks={f.stance: f.output for f in fork_list},
        fork_details=[
            {
                "id": f.id,
                "stance": f.stance,
                "output": f.output,
                "token_count": f.token_count,
                "duration_ms": f.duration_ms,
            }
            for f in fork_list
        ],
        token_usage={
            "forks": total_fork_tokens,
            "synthesis": synthesis_tokens,
            "total": total_tokens,
        },
        duration_ms=overall_duration,
    )


__all__ = [
    "synthesize",
    "Fork",
    "ForkConfig",
    "ForkManager",
    "ForkResult",
    "SelectedStance",
    "StanceSelector",
    "SynthesisEngine",
    "BUILT_IN_STANCES",
    "FORK_OUTPUT_TEMPLATE",
    "SYNTHESIS_SYSTEM_PROMPT",
    "SYNTHESIS_USER_TEMPLATE",
    "get_stance_prompt",
]
