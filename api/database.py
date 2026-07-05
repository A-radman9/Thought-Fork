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
Thought Fork API — SQLite multi-turn session persistence.

Stores sessions and conversational turns.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

import aiosqlite

DB_PATH = os.environ.get("THOUGHT_FORK_DB", "thought_fork_sessions.db")

_CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_CREATE_TURNS_TABLE = """
CREATE TABLE IF NOT EXISTS turns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    parent_turn_id TEXT,
    parent_fork_id TEXT,
    prompt TEXT NOT NULL,
    created_at TEXT NOT NULL,
    fork_outputs TEXT NOT NULL,
    synthesis_output TEXT NOT NULL,
    synthesis_token_count INTEGER NOT NULL DEFAULT 0,
    synthesis_duration_ms INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""

_CREATE_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS cache (
    hash_key TEXT PRIMARY KEY,
    output TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


async def init_db() -> None:
    """Create the sessions and turns tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute(_CREATE_SESSIONS_TABLE)
        await db.execute(_CREATE_TURNS_TABLE)
        await db.execute(_CREATE_CACHE_TABLE)
        
        # Migrations for existing DBs
        try:
            await db.execute("ALTER TABLE turns ADD COLUMN parent_turn_id TEXT")
            await db.execute("ALTER TABLE turns ADD COLUMN parent_fork_id TEXT")
        except Exception:
            pass
            
        await db.commit()


async def create_session(title: str) -> str:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now),
        )
        await db.commit()
    return session_id

async def update_session_title(session_id: str, title: str) -> None:
    """Update the title of an existing session."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, session_id),
        )
        await db.commit()


async def save_turn(
    session_id: str,
    prompt: str,
    fork_outputs: list[dict],
    synthesis_output: str,
    synthesis_token_count: int,
    synthesis_duration_ms: int,
    total_tokens: int,
) -> str:
    """Persist a completed turn in a session. Returns the turn_id."""
    turn_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Insert turn
        await db.execute(
            """
            INSERT INTO turns
                (id, session_id, parent_turn_id, parent_fork_id, prompt, created_at, fork_outputs, synthesis_output,
                 synthesis_token_count, synthesis_duration_ms, total_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                turn_id,
                session_id,
                None,
                None,
                prompt,
                now,
                json.dumps(fork_outputs),
                synthesis_output,
                synthesis_token_count,
                synthesis_duration_ms,
                total_tokens,
            ),
        )
        
        # Update session timestamp
        await db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        await db.commit()
    return turn_id


async def list_sessions(limit: int = 50) -> list[dict]:
    """Retrieve all sessions ordered by updated_at."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


async def get_session(session_id: str) -> dict | None:
    """Retrieve a stored session and all its turns by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get session
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session_row = await cursor.fetchone()
        
        if session_row is None:
            return None
            
        # Get turns
        cursor = await db.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        )
        turn_rows = await cursor.fetchall()
        
        turns = []
        for row in turn_rows:
            turns.append({
                "turn_id": row["id"],
                "prompt": row["prompt"],
                "created_at": row["created_at"],
                "forks": json.loads(row["fork_outputs"]),
                "synthesis": row["synthesis_output"],
                "synthesis_token_count": row["synthesis_token_count"],
                "synthesis_duration_ms": row["synthesis_duration_ms"],
                "total_tokens": row["total_tokens"],
            })
            
        return {
            "session_id": session_row["id"],
            "title": session_row["title"],
            "created_at": session_row["created_at"],
            "updated_at": session_row["updated_at"],
            "turns": turns,
        }

async def get_cached_output(hash_key: str) -> dict | None:
    """Retrieve cached fork output."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cache WHERE hash_key = ?", (hash_key,))
        row = await cursor.fetchone()
        if row:
            return {
                "output": row["output"],
                "token_count": row["token_count"],
                "duration_ms": row["duration_ms"]
            }
        return None

async def set_cached_output(hash_key: str, output: str, token_count: int, duration_ms: int) -> None:
    """Save a fork output to cache."""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO cache (hash_key, output, token_count, duration_ms, created_at) VALUES (?, ?, ?, ?, ?)",
            (hash_key, output, token_count, duration_ms, now)
        )
        await db.commit()

