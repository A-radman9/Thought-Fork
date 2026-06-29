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
Thought Fork — SynthesisEngine.

The SynthesisEngine merges all fork outputs into a single, unified answer.
The key differentiator is *attributed convergence*: the synthesis explicitly
credits which fork contributed each insight, making the reasoning process
transparent.
"""

import os
import time

from openai import AsyncOpenAI

from thought_fork.config import ForkConfig
from thought_fork.fork import Fork


# ---------------------------------------------------------------------------
# Synthesis prompt template
# ---------------------------------------------------------------------------

_SYNTHESIS_SYSTEM_PROMPT = """\
You are the Synthesis Engine in the Thought Fork framework. Your role is to \
merge multiple parallel reasoning paths ("forks") into a single, comprehensive \
and highly structured answer.

Rules:
1. Integrate insights from ALL forks — do not ignore any fork.
2. Explicitly attribute each insight to its source fork using phrases like \
"From the cautious fork..." or "The creative perspective revealed..."
3. Resolve contradictions by explaining the tension and offering a balanced view.
4. USE RICH MARKDOWN: Format your answer beautifully. Use Markdown tables to compare \
viewpoints, bullet points for lists, and clear headers (H2/H3) to structure the synthesis.
5. The final answer should be MORE insightful than any individual fork alone.
6. Keep the attribution natural — weave it into the narrative, but use formatting to make it pop.
"""

_SYNTHESIS_USER_TEMPLATE = """\
Here are {fork_count} parallel reasoning paths for the question:

"{prompt}"

{fork_outputs}

Synthesize these into a unified, comprehensive answer. Explicitly credit which \
fork contributed each insight using natural attribution phrases.\
"""

_FORK_OUTPUT_TEMPLATE = """\
--- Fork {fork_id} ({stance}) ---
{output}
"""


class SynthesisEngine:
    """Merges fork outputs into an attributed synthesis.

    The SynthesisEngine takes all completed fork outputs and sends them to
    a (potentially more capable) AI model with instructions to produce a
    unified answer that explicitly credits each fork's contribution.

    This is the "convergence" step in the Thought Fork framework.

    Args:
        config: ForkConfig controlling model selection and limits.
    """

    def __init__(self, config: ForkConfig | None = None) -> None:
        self.config = config or ForkConfig()
        self._client = AsyncOpenAI(
            base_url=self.config.api_base_url,
            api_key=self.config.api_key,
        )

    async def synthesize(
        self,
        prompt: str,
        forks: list[Fork],
    ) -> tuple[str, int, int]:
        """Synthesize all fork outputs into an attributed final answer.

        Args:
            prompt: The original user prompt.
            forks: List of completed Fork objects with populated outputs.

        Returns:
            A tuple of (synthesis_text, token_count, duration_ms).
        """
        # Build the fork outputs section
        fork_outputs = "\n".join(
            _FORK_OUTPUT_TEMPLATE.format(
                fork_id=fork.id,
                stance=fork.stance,
                output=fork.output,
            )
            for fork in forks
        )

        # Build the user message
        user_message = _SYNTHESIS_USER_TEMPLATE.format(
            fork_count=len(forks),
            prompt=prompt,
            fork_outputs=fork_outputs,
        )

        start_time = time.perf_counter()

        try:
            response = await self._client.chat.completions.create(
                model=self.config.synthesis_model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "system", "content": _SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )

            synthesis_text = response.choices[0].message.content or ""
            token_count = (
                response.usage.completion_tokens if response.usage else 0
            )

        except Exception as e:
            synthesis_text = f"[Synthesis error: {e}]"
            token_count = 0

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        duration_ms = int(elapsed_ms)

        return synthesis_text, token_count, duration_ms
