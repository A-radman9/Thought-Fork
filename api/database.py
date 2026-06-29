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
Thought Fork API — SQLite session persistence.

Stores completed fork sessions so they can be retrieved later via
GET /forks/{session_id}.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import aiosqlite

# Database file location — defaults to project root
DB_PATH = os.environ.get("THOUGHT_FORK_DB", "thought_fork_sessions.db")

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    created_at TEXT NOT NULL,
    fork_outputs TEXT NOT NULL,
    synthesis_output TEXT NOT NULL,
    synthesis_token_count INTEGER NOT NULL DEFAULT 0,
    synthesis_duration_ms INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0
);
"""


async def init_db() -> None:
    """Create the sessions table if it doesn't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


async def save_session(
    session_id: str,
    prompt: str,
    fork_outputs: list[dict],
    synthesis_output: str,
    synthesis_token_count: int,
    synthesis_duration_ms: int,
    total_tokens: int,
) -> None:
    """Persist a completed fork session.

    Args:
        session_id: Unique identifier for this session.
        prompt: The original user prompt.
        fork_outputs: List of fork output dicts with id, stance, output, token_count, duration_ms.
        synthesis_output: The synthesized text.
        synthesis_token_count: Tokens used by the synthesis step.
        synthesis_duration_ms: Duration of the synthesis step in ms.
        total_tokens: Total tokens across all forks + synthesis.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO sessions
                (id, prompt, created_at, fork_outputs, synthesis_output,
                 synthesis_token_count, synthesis_duration_ms, total_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                prompt,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(fork_outputs),
                synthesis_output,
                synthesis_token_count,
                synthesis_duration_ms,
                total_tokens,
            ),
        )
        await db.commit()


async def get_session(session_id: str) -> dict | None:
    """Retrieve a stored fork session by ID.

    Returns:
        A dict with session data, or None if not found.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return {
            "session_id": row["id"],
            "prompt": row["prompt"],
            "created_at": row["created_at"],
            "forks": json.loads(row["fork_outputs"]),
            "synthesis": row["synthesis_output"],
            "synthesis_token_count": row["synthesis_token_count"],
            "synthesis_duration_ms": row["synthesis_duration_ms"],
            "total_tokens": row["total_tokens"],
        }
