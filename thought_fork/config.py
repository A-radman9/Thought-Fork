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
Thought Fork — Configuration and built-in stance definitions.

This module defines the ForkConfig dataclass for controlling fork/synthesis
behavior, and the BUILT_IN_STANCES dictionary mapping stance names to their
system prompts.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Built-in Stances
# ---------------------------------------------------------------------------
# Each stance is a system prompt that biases a fork's reasoning toward a
# specific perspective. These are the stances defined as part of the
# Thought Fork framework (see CONCEPT.md).

BUILT_IN_STANCES: dict[str, str] = {
    "cautious": (
        "You are reasoning from a cautious perspective. "
        "Reason carefully. Identify risks, edge cases, and failure modes first. "
        "Highlight what could go wrong and what safeguards are needed."
    ),
    "creative": (
        "You are reasoning from a creative perspective. "
        "Think laterally. Explore unconventional and non-obvious angles. "
        "Suggest ideas that others might overlook or dismiss too quickly."
    ),
    "critical": (
        "You are reasoning from a critical perspective. "
        "Challenge every assumption. Play devil's advocate. Find the weaknesses. "
        "Question whether the premise itself is correct."
    ),
    "pragmatic": (
        "You are reasoning from a pragmatic perspective. "
        "Focus only on what is immediately practical and resource-efficient. "
        "Prioritize actionable steps over theoretical perfection."
    ),
    "first-principles": (
        "You are reasoning from first principles. "
        "Break everything down to fundamentals. Ignore conventional wisdom. "
        "Rebuild your reasoning from the ground up."
    ),
    "optimistic": (
        "You are reasoning from an optimistic perspective. "
        "Identify best-case outcomes and the path to achieve them. "
        "Focus on opportunities, strengths, and upside potential."
    ),
    "contrarian": (
        "You are reasoning from a contrarian perspective. "
        "Argue the opposite of the obvious answer. "
        "Find value in the position that most people would reject."
    ),
}


# ---------------------------------------------------------------------------
# ForkConfig
# ---------------------------------------------------------------------------

@dataclass
class ForkConfig:
    """Configuration for the Thought Fork engine.

    Attributes:
        fork_model: Model identifier for fork reasoning (fast/cheap).
        synthesis_model: Model identifier for synthesis (quality).
        stance_selector_model: Model used for dynamic stance selection (fast/cheap).
        default_stances: List of stance names used when none are specified and
            dynamic stances are disabled.
        max_tokens: Maximum tokens per fork/synthesis response.
        api_base_url: Base URL for the API (default: OpenRouter).
        use_dynamic_stances: If True (default), uses AI to invent custom stances
            for each prompt. If False, uses default_stances (static built-ins).
    """

    fork_model: str = "anthropic/claude-haiku-4.5"
    synthesis_model: str = "anthropic/claude-sonnet-4-6"
    stance_selector_model: str = "anthropic/claude-haiku-4.5"
    default_stances: list[str] = field(
        default_factory=lambda: ["cautious", "creative", "critical"]
    )
    max_tokens: int = 1024
    api_base_url: str = "https://openrouter.ai/api/v1"
    use_dynamic_stances: bool = True
