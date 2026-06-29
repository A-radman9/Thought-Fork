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
Thought Fork API — Fork routes.

POST /fork  — Start a fork session with SSE streaming
GET  /forks/{session_id} — Retrieve a stored session
"""

from __future__ import annotations

import os
import sys

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

# Add parent path for thought_fork imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.models import ForkRequest, SessionResponse, ForkOutput
from api.streaming import stream_fork_session
from api.database import get_session
from thought_fork.config import ForkConfig, BUILT_IN_STANCES

router = APIRouter()


@router.post("/fork")
async def create_fork(request: ForkRequest):
    """Fork a prompt into parallel reasoning paths with SSE streaming.

    The response is a Server-Sent Events stream. Events arrive in this order:

    1. `fork_start` — one per fork, when it begins
    2. `fork_chunk` — text chunks from each fork (interleaved across all forks)
    3. `fork_done` — one per fork, when it completes
    4. `synthesis_chunk` — text chunks from the synthesis
    5. `synthesis_done` — final event with session_id for retrieval
    """
    # Resolve stances
    if request.stances:
        stances = request.stances[:request.fork_count]
    else:
        default_stances = list(BUILT_IN_STANCES.keys())
        stances = default_stances[: request.fork_count]

    config = ForkConfig()

    return EventSourceResponse(
        stream_fork_session(
            prompt=request.prompt,
            stances=stances,
            config=config,
        ),
        media_type="text/event-stream",
    )


@router.get("/forks/{session_id}", response_model=SessionResponse)
async def get_fork_session(session_id: str):
    """Retrieve a stored fork session by its ID.

    The session_id is returned in the synthesis_done SSE event.
    """
    session = await get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )

    return SessionResponse(
        session_id=session["session_id"],
        prompt=session["prompt"],
        created_at=session["created_at"],
        forks=[
            ForkOutput(
                fork_id=f["fork_id"],
                stance=f["stance"],
                output=f["output"],
                token_count=f["token_count"],
                duration_ms=f["duration_ms"],
            )
            for f in session["forks"]
        ],
        synthesis=session["synthesis"],
        synthesis_token_count=session["synthesis_token_count"],
        synthesis_duration_ms=session["synthesis_duration_ms"],
        total_tokens=session["total_tokens"],
    )
