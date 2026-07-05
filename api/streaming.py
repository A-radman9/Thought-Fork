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
Thought Fork API — Streaming fork execution with interleaved SSE.
"""

from __future__ import annotations

import asyncio
import string
import time
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from api.models import ForkEvent, SelectedStanceModel
from thought_fork.config import ForkConfig
from thought_fork.stance_selector import StanceSelector, SelectedStance
from thought_fork.synthesis import (
    SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_USER_TEMPLATE, FORK_OUTPUT_TEMPLATE,
    DEEP_SYNTHESIS_SYSTEM_PROMPT, DEEP_SYNTHESIS_USER_TEMPLATE
)
from thought_fork.message import Message


async def stream_fork_session(
    prompt: str,
    fork_count: int | str,
    use_dynamic_stances: bool = True,
    session_id: str | None = None,
    manual_stances: list[str] | None = None,
    config: ForkConfig | None = None,
) -> AsyncGenerator[str, None]:
    """Run forks with streaming and yield interleaved SSE events."""
    import hashlib
    import json
    from api.database import get_cached_output, set_cached_output

    config = config or ForkConfig()
    config.use_dynamic_stances = use_dynamic_stances

    client = AsyncOpenAI(
        base_url=config.api_base_url,
        api_key=config.api_key,
    )

    from api.database import get_session, create_session, save_turn, update_session_title

    history: list[Message] = []

    async def _generate_and_update_title(sid: str, p: str):
        try:
            resp = await client.chat.completions.create(
                model=config.stance_selector_model,
                messages=[
                    {"role": "system", "content": "You are a title generator. Generate a concise, 3-5 word title for the user's prompt. Do NOT use quotes, punctuation, or extra words. Just the title itself."},
                    {"role": "user", "content": p}
                ],
                max_tokens=20,
                temperature=0.7,
            )
            title = resp.choices[0].message.content.strip().strip('"\'')
            await update_session_title(sid, title)
        except Exception as e:
            import logging
            logging.error(f"Title generation failed: {e}")
    
    if session_id:
        session = await get_session(session_id)
        if session:
            # Build history from past turns
            for turn in session["turns"]:
                history.append({"role": "user", "content": turn["prompt"]})
                history.append({"role": "assistant", "content": turn["synthesis"]})
        else:
            # Bad session ID, create new
            session_id = await create_session("New Chat")
            asyncio.create_task(_generate_and_update_title(session_id, prompt))
    else:
        # Create new
        session_id = await create_session("New Chat")
        asyncio.create_task(_generate_and_update_title(session_id, prompt))

    letters = string.ascii_uppercase
    queue: asyncio.Queue[ForkEvent | None] = asyncio.Queue()

    # Track completed fork data for synthesis and persistence
    all_fork_results: dict[str, dict] = {}
    current_synthesis_text = ""
    total_token_count = 0
    total_duration_ms = 0

    # 2-Pass Recursive Loop (Pass 1: Initial, Pass 2: Deep Reflection)
    actual_fork_count = 0
    for pass_idx in range(2):
        is_deepen = pass_idx == 1
        
        # -----------------------------------------------------------------------
        # Phase 0: Dynamic Stance Selection
        # -----------------------------------------------------------------------
        selector = StanceSelector(config)
        
        current_fork_count = actual_fork_count if is_deepen and actual_fork_count > 0 else fork_count
        
        selected_stances: list[SelectedStance] = await selector.select(
            prompt, current_fork_count, history=history, 
            manual_stances=manual_stances if not is_deepen else None,
            initial_synthesis=current_synthesis_text if is_deepen else None
        )

        if not is_deepen:
            actual_fork_count = len(selected_stances)

        # Shift letters for pass 2
        if is_deepen:
            for i, s in enumerate(selected_stances):
                s.id = letters[(actual_fork_count * pass_idx + i) % len(letters)]
        
        stances_event = ForkEvent(
            event_type="stances_selected",
            stances=[
                SelectedStanceModel(id=s.id, name=s.name, description=s.description)
                for s in selected_stances
            ],
        )
        yield f"data: {stances_event.model_dump_json()}\n\n"

        # -----------------------------------------------------------------------
        # Phase 1: Parallel Fork Streaming
        # -----------------------------------------------------------------------
        queue: asyncio.Queue[ForkEvent | None] = asyncio.Queue()
        pass_fork_results: dict[str, dict] = {}
        
        previous_forks_text = ""
        if is_deepen and all_fork_results:
            ordered_previous_forks = sorted(all_fork_results.values(), key=lambda f: f["fork_id"])
            previous_forks_text = "\n".join(
                FORK_OUTPUT_TEMPLATE.format(
                    fork_id=f["fork_id"],
                    stance=f["stance"],
                    output=f["output"],
                )
                for f in ordered_previous_forks
            )

        async def _stream_single_fork(stance: SelectedStance) -> None:
            """Stream a single fork and push chunks to the shared queue."""
            await queue.put(ForkEvent(
                event_type="fork_start",
                fork_id=stance.id,
                stance=stance.name,
            ))

            history_str = json.dumps(history) if history else "[]"
            hash_input = f"{prompt}:{stance.name}:{stance.system_prompt}:{history_str}"
            hash_key = hashlib.sha256(hash_input.encode()).hexdigest()
            
            cached = await get_cached_output(hash_key)
            if cached:
                full_output = cached["output"]
                token_count = cached["token_count"]
                elapsed_ms = cached["duration_ms"]
                await queue.put(ForkEvent(
                    event_type="fork_chunk",
                    fork_id=stance.id,
                    stance=stance.name,
                    chunk=full_output,
                ))
            else:
                full_output = ""
                token_count = 0
                start_time = time.perf_counter()
        
                try:
                    messages = [{"role": "system", "content": stance.system_prompt}]
                    if history:
                        messages.extend(history)
                    messages.append({"role": "user", "content": prompt})
                    if is_deepen:
                        # Append the previous synthesis to the user prompt so the fork can critique it
                        messages[-1]["content"] += f"\n\n--- PREVIOUS SYNTHESIS ---\n{current_synthesis_text}"
                        if previous_forks_text:
                            messages[-1]["content"] += f"\n\n--- PREVIOUS EXPERT OPINIONS ---\n{previous_forks_text}"
        
                    model_to_use = config.fork_model
                    if getattr(stance, "assigned_model", "default") != "default":
                        # Validate it's in the allowed list just in case AI hallucinates
                        if stance.assigned_model in config.available_models:
                            model_to_use = stance.assigned_model
                            
                    stream = await client.chat.completions.create(
                        model=model_to_use,
                        max_tokens=config.max_tokens,
                        messages=messages,
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
                    
                await set_cached_output(hash_key, full_output, token_count, elapsed_ms)

            pass_fork_results[stance.id] = {
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

        fork_tasks = [asyncio.create_task(_stream_single_fork(stance)) for stance in selected_stances]

        async def _run_all_forks():
            await asyncio.gather(*fork_tasks)
            await queue.put(None)

        producer = asyncio.create_task(_run_all_forks())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {event.model_dump_json()}\n\n"

        await producer
        
        all_fork_results.update(pass_fork_results)

        # -----------------------------------------------------------------------
        # Phase 2: Synthesis Streaming
        # -----------------------------------------------------------------------
        if is_deepen:
            transition_text = "\n\n---\n\n## Deep Reflection Phase\n\n*Critiquing previous synthesis and applying adversarial experts...*\n\n"
            current_synthesis_text += transition_text
            yield f"data: {ForkEvent(event_type='synthesis_chunk', fork_id='synthesis', chunk=transition_text).model_dump_json()}\n\n"

        ordered_forks = sorted(all_fork_results.values(), key=lambda f: f["fork_id"])

        fork_outputs_text = "\n".join(
            FORK_OUTPUT_TEMPLATE.format(
                fork_id=f["fork_id"],
                stance=f["stance"],
                output=f["output"],
            )
            for f in ordered_forks
        )

        synthesis_user_template = DEEP_SYNTHESIS_USER_TEMPLATE if is_deepen else SYNTHESIS_USER_TEMPLATE
        synthesis_user_msg = synthesis_user_template.format(
            fork_count=len(ordered_forks),
            prompt=prompt,
            fork_outputs=fork_outputs_text,
        )

        synthesis_token_count = 0
        synthesis_start = time.perf_counter()

        try:
            sys_prompt = DEEP_SYNTHESIS_SYSTEM_PROMPT if is_deepen else SYNTHESIS_SYSTEM_PROMPT
            messages = [{"role": "system", "content": sys_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": synthesis_user_msg})

            stream = await client.chat.completions.create(
                model=config.synthesis_model,
                max_tokens=config.synthesis_max_tokens,
                messages=messages,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    current_synthesis_text += text
                    yield f"data: {ForkEvent(event_type='synthesis_chunk', fork_id='synthesis', chunk=text).model_dump_json()}\n\n"

                if hasattr(chunk, "usage") and chunk.usage:
                    synthesis_token_count = chunk.usage.completion_tokens or 0

        except Exception as e:
            error_msg = f"[Synthesis error: {e}]"
            current_synthesis_text += error_msg
            yield f"data: {ForkEvent(event_type='synthesis_chunk', fork_id='synthesis', chunk=error_msg).model_dump_json()}\n\n"

        synthesis_duration_ms = int((time.perf_counter() - synthesis_start) * 1000)
        
        if synthesis_token_count == 0:
            synthesis_token_count = len(current_synthesis_text.split()) * 4 // 3
            
        total_token_count += sum(f["token_count"] for f in pass_fork_results.values()) + synthesis_token_count
        total_duration_ms += synthesis_duration_ms
        
        if is_deepen:
            done_event = ForkEvent(
                event_type="synthesis_done",
                fork_id="synthesis",
                is_done=True,
                token_count=synthesis_token_count,
                duration_ms=total_duration_ms,
                session_id=session_id,
            )
            yield f"data: {done_event.model_dump_json()}\n\n"

    # -----------------------------------------------------------------------
    # Phase 3: Persist turn
    # -----------------------------------------------------------------------
    final_ordered_forks = sorted(all_fork_results.values(), key=lambda f: f["fork_id"])
    await save_turn(
        session_id=session_id,
        prompt=prompt,
        fork_outputs=final_ordered_forks,
        synthesis_output=current_synthesis_text,
        synthesis_token_count=total_token_count, # Using total_token_count
        synthesis_duration_ms=total_duration_ms,
        total_tokens=total_token_count,
    )
