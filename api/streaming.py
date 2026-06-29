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

This module handles the core streaming logic:
  Phase 0: Dynamic stance selection (AI picks the best perspectives)
  Phase 1: Parallel fork streaming (interleaved SSE chunks)
  Phase 2: Synthesis streaming
  Phase 3: Session persistence to SQLite
"""

from __future__ import annotations

import asyncio
import os
import string
import time
import uuid
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from api.models import ForkEvent, SelectedStanceModel

# Add parent path for thought_fork imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from thought_fork.config import ForkConfig
from thought_fork.stance_selector import StanceSelector, SelectedStance
from thought_fork.synthesis import _SYNTHESIS_SYSTEM_PROMPT, _SYNTHESIS_USER_TEMPLATE, _FORK_OUTPUT_TEMPLATE


async def stream_fork_session(
    prompt: str,
    fork_count: int,
    use_dynamic_stances: bool = True,
    config: ForkConfig | None = None,
) -> AsyncGenerator[str, None]:
    """Run forks with streaming and yield interleaved SSE events.

    Phase 0 — Dynamic Stance Selection:
        Calls StanceSelector to invent N reasoning perspectives for this
        specific prompt. Emits a `stances_selected` event immediately so
        the UI can show the selected stances before any fork starts.

    Phase 1 — Parallel Fork Streaming:
        Spawns N fork streams concurrently. Chunks from all forks are
        pushed to a shared asyncio.Queue and yielded interleaved.

    Phase 2 — Synthesis Streaming:
        After all forks complete, streams the synthesis response.

    Phase 3 — Persistence:
        Saves the completed session to SQLite.

    Args:
        prompt: The user's question.
        fork_count: Number of parallel forks to spawn.
        use_dynamic_stances: If True, use AI to select stances dynamically.
        config: Optional ForkConfig override.

    Yields:
        JSON-encoded ForkEvent strings, one per SSE event.
    """
    config = config or ForkConfig()
    config.use_dynamic_stances = use_dynamic_stances

    client = AsyncOpenAI(
        base_url=config.api_base_url,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    session_id = uuid.uuid4().hex[:12]
    letters = string.ascii_uppercase
    queue: asyncio.Queue[ForkEvent | None] = asyncio.Queue()

    # Track completed fork data for synthesis and persistence
    fork_results: dict[str, dict] = {}

    # -----------------------------------------------------------------------
    # Phase 0: Dynamic Stance Selection
    # -----------------------------------------------------------------------
    selector = StanceSelector(config)
    selected_stances: list[SelectedStance] = await selector.select(
        prompt, fork_count
    )

    # Emit stances_selected event immediately so the UI can show the selections
    stances_event = ForkEvent(
        event_type="stances_selected",
        stances=[
            SelectedStanceModel(
                id=s.id,
                name=s.name,
                description=s.description,
            )
            for s in selected_stances
        ],
    )
    yield f"data: {stances_event.model_dump_json()}\n\n"

    # -----------------------------------------------------------------------
    # Phase 1: Parallel Fork Streaming
    # -----------------------------------------------------------------------

    async def _stream_single_fork(stance: SelectedStance) -> None:
        """Stream a single fork and push chunks to the shared queue."""
        await queue.put(ForkEvent(
            event_type="fork_start",
            fork_id=stance.id,
            stance=stance.name,
        ))

        full_output = ""
        token_count = 0
        start_time = time.perf_counter()

        try:
            stream = await client.chat.completions.create(
                model=config.fork_model,
                max_tokens=config.max_tokens,
                messages=[
                    {"role": "system", "content": stance.system_prompt},
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
                        fork_id=stance.id,
                        stance=stance.name,
                        chunk=text,
                    ))

                if hasattr(chunk, "usage") and chunk.usage:
                    token_count = chunk.usage.completion_tokens or 0

        except Exception as e:
            full_output = f"[Fork {stance.id} error: {e}]"
            await queue.put(ForkEvent(
                event_type="fork_chunk",
                fork_id=stance.id,
                stance=stance.name,
                chunk=full_output,
            ))

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        if token_count == 0:
            token_count = len(full_output.split()) * 4 // 3

        fork_results[stance.id] = {
            "fork_id": stance.id,
            "stance": stance.name,
            "output": full_output,
            "token_count": token_count,
            "duration_ms": elapsed_ms,
        }

        await queue.put(ForkEvent(
            event_type="fork_done",
            fork_id=stance.id,
            stance=stance.name,
            is_done=True,
            token_count=token_count,
            duration_ms=elapsed_ms,
        ))

    # Spawn all fork tasks concurrently
    fork_tasks = [
        asyncio.create_task(_stream_single_fork(stance))
        for stance in selected_stances
    ]

    async def _run_all_forks():
        await asyncio.gather(*fork_tasks)
        await queue.put(None)  # sentinel

    producer = asyncio.create_task(_run_all_forks())

    while True:
        event = await queue.get()
        if event is None:
            break
        yield f"data: {event.model_dump_json()}\n\n"

    await producer

    # -----------------------------------------------------------------------
    # Phase 2: Synthesis Streaming
    # -----------------------------------------------------------------------
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
        yield f"data: {ForkEvent(event_type='synthesis_chunk', fork_id='synthesis', chunk=synthesis_text).model_dump_json()}\n\n"

    synthesis_duration_ms = int((time.perf_counter() - synthesis_start) * 1000)

    if synthesis_token_count == 0:
        synthesis_token_count = len(synthesis_text.split()) * 4 // 3

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
    # Phase 3: Persist session
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
