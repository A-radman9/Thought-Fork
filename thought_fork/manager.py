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
Thought Fork — ForkManager.

The ForkManager is responsible for creating Fork objects from a prompt and
a list of stances, then running all forks concurrently using asyncio.
Each fork calls an AI model with a stance-specific system prompt.
"""

import asyncio
import logging
import string
import time

from openai import AsyncOpenAI

from thought_fork.config import ForkConfig
from thought_fork.fork import Fork, get_stance_prompt
from thought_fork.message import Message


logger = logging.getLogger("thought_fork.manager")


class ForkManager:
    """Creates and runs parallel reasoning forks.

    The ForkManager spawns N forks from a single user prompt, each biased
    by a different stance via its system prompt. All forks execute
    concurrently using asyncio.gather() for true parallelism.

    Args:
        config: ForkConfig controlling model selection, stances, and limits.
    """

    def __init__(self, config: ForkConfig | None = None) -> None:
        self.config = config or ForkConfig()
        
        # Use provided client (BYOC) or create a new one
        if self.config.client:
            self._client = self.config.client
            logger.debug("ForkManager initialized with custom AsyncOpenAI client")
        else:
            self._client = AsyncOpenAI(
                base_url=self.config.api_base_url,
                api_key=self.config.api_key,
            )
            logger.debug("ForkManager initialized with default AsyncOpenAI client")
            
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_forks)

    def create_forks(
        self,
        prompt: str,
        stances: list[str] | None = None,
    ) -> list[Fork]:
        """Create Fork objects for each stance.

        Args:
            prompt: The user's question or problem to fork.
            stances: List of stance names. Defaults to config.default_stances.

        Returns:
            A list of Fork objects ready for execution.
        """
        stances = stances or self.config.default_stances
        letters = string.ascii_uppercase

        forks = []
        for i, stance in enumerate(stances):
            fork = Fork(
                id=letters[i] if i < len(letters) else str(i),
                stance=stance,
                system_prompt=get_stance_prompt(stance),
            )
            forks.append(fork)

        return forks

    async def _run_single_fork(
        self,
        fork: Fork,
        prompt: str,
        history: list[Message] | None = None,
    ) -> Fork:
        """Execute a single fork by calling the AI model.

        Args:
            fork: The Fork object to execute.
            prompt: The user's original prompt.

        Returns:
            The same Fork object with output, token_count, and duration_ms populated.
        """
        start_time = time.perf_counter()
        
        retries = 0
        max_retries = self.config.max_retries
        
        async with self._semaphore:
            while retries <= max_retries:
                try:
                    logger.debug(f"Fork {fork.id} starting (attempt {retries + 1})")
                    messages = [{"role": "system", "content": fork.system_prompt}]
                    if history:
                        messages.extend(history)
                    messages.append({"role": "user", "content": prompt})

                    response = await asyncio.wait_for(
                        self._client.chat.completions.create(
                            model=self.config.fork_model,
                            max_tokens=self.config.max_tokens,
                            messages=messages,
                        ),
                        timeout=self.config.timeout_seconds,
                    )
        
                    fork.output = response.choices[0].message.content or ""
                    fork.token_count = (
                        response.usage.completion_tokens if response.usage else 0
                    )
                    logger.debug(f"Fork {fork.id} completed successfully")
                    break  # Success, exit retry loop
                    
                except asyncio.TimeoutError:
                    if retries < max_retries:
                        logger.warning(f"Fork {fork.id} timed out. Retrying...")
                        retries += 1
                        await asyncio.sleep(2 ** retries)  # Exponential backoff: 2s, 4s
                    else:
                        logger.error(f"Fork {fork.id} failed: Timeout after {max_retries} retries")
                        fork.output = f"[Fork {fork.id} failed: timed out after {self.config.timeout_seconds}s]"
                        break
                        
                except Exception as e:
                    if retries < max_retries:
                        logger.warning(f"Fork {fork.id} encountered error: {e}. Retrying...")
                        retries += 1
                        await asyncio.sleep(2 ** retries)
                    else:
                        logger.error(f"Fork {fork.id} failed permanently: {e}")
                        fork.output = f"[Fork {fork.id} failed: {e}]"
                        break
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        fork.duration_ms = int(elapsed_ms)
        
        return fork

    async def run_parallel(
        self,
        forks: list[Fork],
        prompt: str,
        history: list[Message] | None = None,
    ) -> list[Fork]:
        """Run all forks concurrently using asyncio.gather().

        This is the core of Thought Fork's parallel execution model.
        All forks fire simultaneously — the total wall-clock time should
        be approximately equal to the slowest fork, not the sum.

        Args:
            forks: List of Fork objects to execute.
            prompt: The user's original prompt.

        Returns:
            The same list of Fork objects, now with outputs populated.
        """
        logger.info(f"Running {len(forks)} forks in parallel (max_concurrent={self.config.max_concurrent_forks})")
        tasks = [self._run_single_fork(fork, prompt, history) for fork in forks]
        completed = await asyncio.gather(*tasks)
        return list(completed)
