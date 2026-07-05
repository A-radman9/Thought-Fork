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
Thought Fork API — Fork routes.

POST /fork  — Start a fork session with SSE streaming
GET  /sessions — List all chat sessions
GET  /sessions/{session_id} — Retrieve a stored session and its conversational turns
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from api.models import ForkRequest, SessionResponse, SessionListResponse, TurnOutput, ForkOutput
from api.streaming import stream_fork_session
from api.database import get_session, list_sessions
from thought_fork.config import ForkConfig

router = APIRouter()


@router.post("/fork")
async def create_fork(request: ForkRequest):
    """Fork a prompt into parallel reasoning paths with SSE streaming."""
    config = ForkConfig()

    return EventSourceResponse(
        stream_fork_session(
            prompt=request.prompt,
            fork_count=request.fork_count,
            use_dynamic_stances=request.use_dynamic_stances,
            session_id=request.session_id,
            manual_stances=request.stances,
            config=config,
        ),
        media_type="text/event-stream",
    )


@router.get("/sessions", response_model=list[SessionListResponse])
async def get_all_sessions():
    """Retrieve all stored sessions for the sidebar."""
    sessions = await list_sessions(limit=50)
    return [SessionListResponse(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_fork_session(session_id: str):
    """Retrieve a stored fork session by its ID."""
    session = await get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )

    return SessionResponse(
        session_id=session["session_id"],
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        turns=[
            TurnOutput(
                turn_id=t["turn_id"],
                prompt=t["prompt"],
                created_at=t["created_at"],
                forks=[
                    ForkOutput(
                        fork_id=f["fork_id"],
                        stance=f["stance"],
                        output=f["output"],
                        token_count=f["token_count"],
                        duration_ms=f["duration_ms"],
                    )
                    for f in t["forks"]
                ],
                synthesis=t["synthesis"],
                synthesis_token_count=t["synthesis_token_count"],
                synthesis_duration_ms=t["synthesis_duration_ms"],
                total_tokens=t["total_tokens"],
            )
            for t in session["turns"]
        ],
    )
