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
from thought_fork.message import Message


# ---------------------------------------------------------------------------
# Synthesis prompt template
# ---------------------------------------------------------------------------

SYNTHESIS_SYSTEM_PROMPT = """\
You are an elite Synthesis Engine — the intellectual backbone of the Thought Fork framework. \
Your purpose is to take multiple expert reasoning paths ("forks") and forge them into a single \
answer that is dramatically more powerful than any individual fork could achieve alone.

You are NOT a summarizer. You are a synthesizer. The difference is critical:
- A summarizer lists what each fork said. NEVER do this.
- A synthesizer creates NEW insight by finding the intersections, tensions, and emergent \
patterns BETWEEN the forks that no single fork could see on its own.

Rules:
1. DEPTH OVER BREADTH: Go deep. A thorough exploration of 3 key insights beats a shallow \
list of 10 points. Think like a senior advisor writing a brief for a CEO — every sentence \
must earn its place.
2. ATTRIBUTED CONVERGENCE: Weave fork attributions naturally into your prose. \
Use phrases like "The risk-analyst perspective reveals…" or "Where the systems-architect \
and the behavioral-economist diverge is…" — but NEVER create a section that just lists \
"Fork A said X, Fork B said Y." That is summarizing, not synthesizing.
3. SURFACE THE TENSIONS: When forks disagree, this is the most valuable part. Don't \
smooth over disagreements — illuminate them. Explain WHY experts with different lenses \
reach different conclusions, and what that tension reveals about the problem's true complexity.
4. ADAPTIVE FORMAT: Match your output format to the question's domain. \
Code questions get code blocks with analysis. Strategy questions get structured arguments. \
Technical deep-dives get diagrams described in detail. Creative questions get flowing prose. \
NEVER force tables or bullet lists unless they genuinely serve the content.
5. PRODUCE ACTIONABLE INSIGHT: End with something the reader can actually USE — a decision \
framework, a concrete next step, a key question to answer, or a mental model to apply. \
Not a generic "in conclusion, it depends" copout.
6. WRITE AT AN EXPERT LEVEL: Assume the reader is intelligent. Use precise domain terminology. \
6. WRITE AT AN EXPERT LEVEL: Assume the reader is intelligent. Use precise domain terminology. \
Build sophisticated arguments. Show your reasoning chain, not just your conclusions.
"""

DEEP_SYNTHESIS_SYSTEM_PROMPT = """\
You are an elite Adversarial Synthesis Engine. You have been given the outputs of an initial \
synthesis AND a new set of highly specialized, adversarial experts who were specifically designed \
to attack, critique, and tear down that first synthesis.

Your job is NOT to just summarize all the forks. Your job is to produce a FINAL, BULLETPROOF \
conclusion by taking the original ideas and subjecting them to the ruthless crucible of the new adversarial critiques.

Rules:
1. ACKNOWLEDGE THE CRITIQUE: Explicitly highlight how the new adversarial experts exposed flaws, \
loopholes, or shallow assumptions in the initial analysis.
2. REWRITE, DON'T REPEAT: Do not just output the same points as the first synthesis. The final \
answer must represent an EVOLUTION of thought — it must be visibly deeper, more nuanced, and more robust \
than the first attempt.
3. ADAPTIVE FORMAT: Match your output format to the domain.
4. ACTIONABLE CLOSURE: End with a highly concrete, practically applicable framework or decision model \
that survives the adversarial scrutiny.
"""

SYNTHESIS_USER_TEMPLATE = """\
The following {fork_count} expert reasoning paths have analyzed this question from \
fundamentally different intellectual angles:

"{prompt}"

{fork_outputs}

Now synthesize. Do NOT summarize each fork sequentially. Instead:
1. Identify the 2-3 deepest insights that EMERGE from the intersection of these perspectives.
2. Surface the most important tension or disagreement between the forks and explain what it reveals.
3. Forge a unified answer that is richer than any single fork, with natural attribution woven in.
4. Close with a sharp, actionable takeaway.\
"""

DEEP_SYNTHESIS_USER_TEMPLATE = """\
We have executed a 2-pass recursive reasoning loop. 

FIRST PASS (Initial Perspectives):
Forks A, B, and C generated our first draft analysis.

SECOND PASS (Adversarial Critique):
Forks D, E, and F are new, hyper-specialized adversarial experts designed specifically to attack the weaknesses in the first draft.

Here are the outputs from ALL {fork_count} forks:

"{prompt}"

{fork_outputs}

Now synthesize the FINAL answer. 
Do NOT just summarize the 6 forks. You must:
1. Explain how the adversarial forks (D, E, F) dismantled or complicated the initial ideas from (A, B, C).
2. Forge a final, evolved conclusion that survives this intense scrutiny.
3. The final answer MUST NOT be a repeat of the first synthesis. It must represent a higher level of intellectual rigor.\
"""

FORK_OUTPUT_TEMPLATE = """\
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
        history: list[Message] | None = None,
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
            FORK_OUTPUT_TEMPLATE.format(
                fork_id=fork.id,
                stance=fork.stance,
                output=fork.output,
            )
            for fork in forks
        )

        # Build the user message
        user_message = SYNTHESIS_USER_TEMPLATE.format(
            fork_count=len(forks),
            prompt=prompt,
            fork_outputs=fork_outputs,
        )

        start_time = time.perf_counter()

        try:
            messages = [{"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            response = await self._client.chat.completions.create(
                model=self.config.synthesis_model,
                max_tokens=self.config.synthesis_max_tokens,
                messages=messages,
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
