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
    stances: list[str] | None = Field(
        default=None,
        description=(
            "List of stance names for each fork. If omitted, uses the first "
            "N default stances. Available: cautious, creative, critical, "
            "pragmatic, first-principles, optimistic, contrarian."
        ),
    )


# ---------------------------------------------------------------------------
# SSE event model
# ---------------------------------------------------------------------------

class ForkEvent(BaseModel):
    """A single Server-Sent Event emitted during fork streaming.

    Events flow in this order:
    1. fork_start — one per fork, emitted when a fork begins
    2. fork_chunk — streamed text chunks from each fork (interleaved)
    3. fork_done — one per fork, emitted when a fork completes
    4. synthesis_chunk — streamed text chunks from the synthesis
    5. synthesis_done — final event with session_id
    """

    event_type: str = Field(
        ...,
        description="One of: fork_start, fork_chunk, fork_done, synthesis_chunk, synthesis_done",
    )
    fork_id: str | None = Field(
        default=None,
        description="Fork letter ID (A, B, C, ...) or 'synthesis'.",
    )
    stance: str | None = Field(
        default=None,
        description="The fork's stance (null for synthesis events).",
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
