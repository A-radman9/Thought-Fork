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
Thought Fork API — Pydantic request/response models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SelectedStanceModel(BaseModel):
    """A dynamically-selected stance, carried in the stances_selected SSE event."""

    id: str = Field(..., description="Fork letter ID (A, B, C, ...).")
    name: str = Field(..., description="Kebab-case stance name, e.g. 'risk-analyst'.")
    description: str = Field(..., description="One sentence describing this perspective.")


class ForkRequest(BaseModel):
    """Request body for the POST /fork endpoint."""

    prompt: str = Field(
        ...,
        description="The question or problem to fork into parallel reasoning paths.",
        min_length=1,
    )
    fork_count: int = Field(
        default=3,
        ge=2,
        le=7,
        description="Number of parallel forks to spawn (2–7).",
    )
    use_dynamic_stances: bool = Field(
        default=True,
        description=(
            "If True (default), the AI selects the best stances for this prompt. "
            "If False, uses the first N built-in stances (cautious, creative, critical...)."
        ),
    )


# ---------------------------------------------------------------------------
# SSE event model
# ---------------------------------------------------------------------------

class ForkEvent(BaseModel):
    """A single Server-Sent Event emitted during fork streaming.

    Events flow in this order:
    1. stances_selected — fires once before any fork starts, carries chosen stances
    2. fork_start — one per fork, emitted when a fork begins
    3. fork_chunk — streamed text chunks from each fork (interleaved)
    4. fork_done — one per fork, emitted when a fork completes
    5. synthesis_chunk — streamed text chunks from the synthesis
    6. synthesis_done — final event with session_id
    """

    event_type: str = Field(
        ...,
        description=(
            "One of: stances_selected, fork_start, fork_chunk, fork_done, "
            "synthesis_chunk, synthesis_done"
        ),
    )
    fork_id: str | None = Field(
        default=None,
        description="Fork letter ID (A, B, C, ...) or 'synthesis'.",
    )
    stance: str | None = Field(
        default=None,
        description="The fork's stance name (null for stances_selected and synthesis events).",
    )
    stances: list[SelectedStanceModel] | None = Field(
        default=None,
        description="Only present in stances_selected event.",
    )
    chunk: str | None = Field(
        default=None,
        description="A text chunk of the fork/synthesis output.",
    )
    is_done: bool = Field(
        default=False,
        description="True when this fork or the synthesis has finished.",
    )
    token_count: int | None = Field(
        default=None,
        description="Token count (only present in done events).",
    )
    duration_ms: int | None = Field(
        default=None,
        description="Duration in ms (only present in done events).",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID (only present in synthesis_done event).",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ForkOutput(BaseModel):
    """A single fork's output in a stored session."""

    fork_id: str
    stance: str
    output: str
    token_count: int
    duration_ms: int


class SessionResponse(BaseModel):
    """Response for GET /forks/{session_id}."""

    session_id: str
    prompt: str
    created_at: str
    forks: list[ForkOutput]
    synthesis: str
    synthesis_token_count: int
    synthesis_duration_ms: int
    total_tokens: int


class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str = "ok"
    version: str
    engine: str = "Thought Fork"
