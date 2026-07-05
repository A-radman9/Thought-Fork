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
Thought Fork — ForkResult dataclass.

The structured return type from the synthesize() entry point.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ForkResult:
    """The result of a complete Thought Fork session.

    Returned by the top-level ``synthesize()`` function. Contains the
    synthesized answer, individual fork outputs, and usage statistics.

    Attributes:
        synthesis: The merged, attributed final answer.
        forks: Dict mapping stance name → fork output text.
        fork_details: Full fork data including id, stance, output, tokens, duration.
        token_usage: Token counts: {"forks": int, "synthesis": int, "total": int}.
        duration_ms: Total wall-clock time in milliseconds.
    """

    synthesis: str
    forks: dict[str, str] = field(default_factory=dict)
    fork_details: list[dict] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    duration_ms: int = 0
