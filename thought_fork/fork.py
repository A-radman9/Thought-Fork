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
Thought Fork — Fork dataclass and stance resolution.

A Fork represents a single parallel reasoning path. Each fork has a stance
(its reasoning perspective) and a system prompt that biases the AI toward
that stance.
"""

from dataclasses import dataclass

from thought_fork.config import BUILT_IN_STANCES


@dataclass
class Fork:
    """A single parallel reasoning path in the Thought Fork framework.

    Attributes:
        id: Letter identifier for this fork ("A", "B", "C", ...).
        stance: The reasoning perspective (e.g., "cautious", "creative").
        system_prompt: The full system prompt that biases reasoning.
        output: The fork's generated reasoning output (populated after execution).
        token_count: Number of tokens used in the response (populated after execution).
        duration_ms: Execution time in milliseconds (populated after execution).
    """

    id: str
    stance: str
    system_prompt: str
    output: str = ""
    token_count: int = 0
    duration_ms: int = 0


def get_stance_prompt(stance: str) -> str:
    """Resolve a stance name to its system prompt.

    If the stance name matches a built-in stance, returns that prompt.
    Otherwise, treats the stance string itself as a custom system prompt.

    Args:
        stance: A built-in stance name (e.g., "cautious") or a custom prompt string.

    Returns:
        The resolved system prompt for the given stance.
    """
    return BUILT_IN_STANCES.get(stance, stance)
