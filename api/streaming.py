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
Thought Fork API — Streaming fork execution with interleaved SSE.

This module handles the core streaming logic: running multiple forks
concurrently with interleaved chunk output, then streaming the synthesis.
All chunks are pushed to an asyncio.Queue so the SSE endpoint can yield
them in real-time.
"""

from __future__ import annotations

import asyncio
import json
import os
import string
import time
import uuid
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from api.models import ForkEvent

# Add parent path for thought_fork imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from thought_fork.config import ForkConfig, BUILT_IN_STANCES
from thought_fork.synthesis import _SYNTHESIS_SYSTEM_PROMPT, _SYNTHESIS_USER_TEMPLATE, _FORK_OUTPUT_TEMPLATE


async def stream_fork_session(
    prompt: str,
    stances: list[str],
    config: ForkConfig | None = None,
) -> AsyncGenerator[str, None]:
    """Run forks with streaming and yield interleaved SSE events.

    This is the heart of the Phase 2 API. It:
    1. Spawns N fork streams concurrently
    2. Collects chunks from all forks into a shared queue (interleaved)
    3. Yields each chunk as an SSE-formatted JSON event
    4. After all forks complete, streams the synthesis
    5. Saves the session to SQLite

    Args:
        prompt: The user's question.
        stances: List of stance names for each fork.
        config: Optional ForkConfig override.

    Yields:
        JSON-encoded ForkEvent strings, one per SSE event.
    """
    config = config or ForkConfig()
    client = AsyncOpenAI(
        base_url=config.api_base_url,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    session_id = uuid.uuid4().hex[:12]
    letters = string.ascii_uppercase
    queue: asyncio.Queue[ForkEvent | None] = asyncio.Queue()

    # Track completed fork data for synthesis and persistence
    fork_results: dict[str, dict] = {}

    async def _stream_single_fork(index: int, stance: str) -> None:
        """Stream a single fork and push chunks to the shared queue."""
        fork_id = letters[index] if index < len(letters) else str(index)
        system_prompt = BUILT_IN_STANCES.get(stance, stance)

        # Emit fork_start event
        await queue.put(ForkEvent(
            event_type="fork_start",
            fork_id=fork_id,
            stance=stance,
        ))

        full_output = ""
        token_count = 0
        start_time = time.perf_counter()

        try:
            stream = await client.chat.completions.create(
                model=config.fork_model,
                max_tokens=config.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_output += text
                    await queue.put(ForkEvent(
                        event_type="fork_chunk",
                        fork_id=fork_id,
                        stance=stance,
                        chunk=text,
                    ))

                # Capture usage from the final chunk if available
                if hasattr(chunk, "usage") and chunk.usage:
                    token_count = chunk.usage.completion_tokens or 0

        except Exception as e:
            full_output = f"[Fork {fork_id} error: {e}]"
            await queue.put(ForkEvent(
                event_type="fork_chunk",
                fork_id=fork_id,
                stance=stance,
                chunk=full_output,
            ))

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # If no usage was reported via streaming, estimate from output
        if token_count == 0:
            token_count = len(full_output.split()) * 4 // 3  # rough estimate

        fork_results[fork_id] = {
            "fork_id": fork_id,
            "stance": stance,
            "output": full_output,
            "token_count": token_count,
            "duration_ms": elapsed_ms,
        }

        await queue.put(ForkEvent(
            event_type="fork_done",
            fork_id=fork_id,
            stance=stance,
            is_done=True,
            token_count=token_count,
            duration_ms=elapsed_ms,
        ))

    # -----------------------------------------------------------------------
    # Phase 1: Stream all forks concurrently
    # -----------------------------------------------------------------------
    fork_tasks = [
        asyncio.create_task(_stream_single_fork(i, stance))
        for i, stance in enumerate(stances)
    ]

    # Consumer: yield events as they arrive from all forks
    completed_forks = 0
    total_forks = len(stances)

    # Producer task that signals completion
    async def _run_all_forks():
        await asyncio.gather(*fork_tasks)
        await queue.put(None)  # sentinel

    producer = asyncio.create_task(_run_all_forks())

    while True:
        event = await queue.get()
        if event is None:
            break
        yield f"data: {event.model_dump_json()}\n\n"

    await producer  # ensure cleanup

    # -----------------------------------------------------------------------
    # Phase 2: Stream synthesis
    # -----------------------------------------------------------------------
    # Build synthesis prompt from fork results
    ordered_forks = sorted(fork_results.values(), key=lambda f: f["fork_id"])

    fork_outputs_text = "\n".join(
        _FORK_OUTPUT_TEMPLATE.format(
            fork_id=f["fork_id"],
            stance=f["stance"],
            output=f["output"],
        )
        for f in ordered_forks
    )

    synthesis_user_msg = _SYNTHESIS_USER_TEMPLATE.format(
        fork_count=len(ordered_forks),
        prompt=prompt,
        fork_outputs=fork_outputs_text,
    )

    synthesis_text = ""
    synthesis_token_count = 0
    synthesis_start = time.perf_counter()

    try:
        stream = await client.chat.completions.create(
            model=config.synthesis_model,
            max_tokens=config.max_tokens,
            messages=[
                {"role": "system", "content": _SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": synthesis_user_msg},
            ],
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                synthesis_text += text
                event = ForkEvent(
                    event_type="synthesis_chunk",
                    fork_id="synthesis",
                    chunk=text,
                )
                yield f"data: {event.model_dump_json()}\n\n"

            if hasattr(chunk, "usage") and chunk.usage:
                synthesis_token_count = chunk.usage.completion_tokens or 0

    except Exception as e:
        synthesis_text = f"[Synthesis error: {e}]"
        event = ForkEvent(
            event_type="synthesis_chunk",
            fork_id="synthesis",
            chunk=synthesis_text,
        )
        yield f"data: {event.model_dump_json()}\n\n"

    synthesis_duration_ms = int((time.perf_counter() - synthesis_start) * 1000)

    if synthesis_token_count == 0:
        synthesis_token_count = len(synthesis_text.split()) * 4 // 3

    # Final done event
    total_tokens = sum(f["token_count"] for f in fork_results.values()) + synthesis_token_count

    done_event = ForkEvent(
        event_type="synthesis_done",
        fork_id="synthesis",
        is_done=True,
        token_count=synthesis_token_count,
        duration_ms=synthesis_duration_ms,
        session_id=session_id,
    )
    yield f"data: {done_event.model_dump_json()}\n\n"

    # -----------------------------------------------------------------------
    # Persist session
    # -----------------------------------------------------------------------
    from api.database import save_session

    await save_session(
        session_id=session_id,
        prompt=prompt,
        fork_outputs=ordered_forks,
        synthesis_output=synthesis_text,
        synthesis_token_count=synthesis_token_count,
        synthesis_duration_ms=synthesis_duration_ms,
        total_tokens=total_tokens,
    )
