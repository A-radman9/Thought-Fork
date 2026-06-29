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
Thought Fork — Dynamic Stance Selector.

The StanceSelector reads a user's prompt and uses a fast AI call to
invent the N most insightful and complementary reasoning perspectives
for that specific question. Each perspective gets a custom name,
description, and system prompt — all tailored to the prompt.

This is the core of the "Dynamic Stance Selection" feature introduced
in v0.5.0. It replaces the static built-in stance list with AI-generated
perspectives that are unique to every question asked.

Concept by Ameen Saeed, June 2026.
"""

from __future__ import annotations

import json
import os
import string
from dataclasses import dataclass

from openai import AsyncOpenAI

from thought_fork.config import BUILT_IN_STANCES, ForkConfig
from thought_fork.fork import Fork


# ---------------------------------------------------------------------------
# SelectedStance dataclass
# ---------------------------------------------------------------------------

@dataclass
class SelectedStance:
    """A dynamically-chosen reasoning perspective for a specific prompt.

    Attributes:
        id: Fork letter (A, B, C, ...).
        name: Short kebab-case label invented by the AI (e.g. "risk-analyst").
        description: One sentence describing this perspective's angle.
        system_prompt: The full system prompt for this perspective.
    """
    id: str
    name: str
    description: str
    system_prompt: str


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_SELECTOR_SYSTEM = (
    "You are a reasoning architect for the Thought Fork AI framework. "
    "Your job is to analyze a user's question and select the most insightful, "
    "distinct, and complementary reasoning perspectives to examine it from. "
    "Each perspective must approach the problem from a genuinely different angle — "
    "not just rephrases of the same viewpoint. "
    "Be specific and creative. Avoid generic names like 'balanced' or 'general'. "
    "Return ONLY a valid JSON array. No explanation, no markdown, no prose. "
    "Just raw JSON."
)

_SELECTOR_USER_TEMPLATE = (
    "Select exactly {n} reasoning perspectives for this question.\n\n"
    "Question: {q}\n\n"
    "Return a JSON array with exactly {n} objects. Each object must have:\n"
    '- "name": short kebab-case label (e.g. "risk-analyst", "contrarian-economist")\n'
    '- "description": one sentence explaining this perspective\'s unique angle\n'
    '- "system_prompt": 2-3 sentences defining the role, mindset, and focus area'
)


# ---------------------------------------------------------------------------
# StanceSelector
# ---------------------------------------------------------------------------

class StanceSelector:
    """Dynamically selects reasoning stances tailored to a specific prompt.

    Uses a fast, cheap AI model to analyze the prompt and invent N
    complementary perspectives. Falls back to built-in stances if the
    AI response cannot be parsed.

    Args:
        config: ForkConfig controlling model selection and API base URL.
    """

    def __init__(self, config: ForkConfig | None = None) -> None:
        self.config = config or ForkConfig()
        self._client = AsyncOpenAI(
            base_url=self.config.api_base_url,
            api_key=self.config.api_key,
        )

    async def select(
        self,
        prompt: str,
        fork_count: int = 3,
    ) -> list[SelectedStance]:
        """Select dynamic stances for a given prompt.

        Makes a single, fast, non-streaming AI call to invent N reasoning
        perspectives tailored to the specific prompt. If the AI returns
        invalid JSON or the wrong structure, falls back silently to built-in
        stances so the user always gets a result.

        Args:
            prompt: The user's question to analyze.
            fork_count: Number of stances to select.

        Returns:
            A list of SelectedStance objects — one per fork.
        """
        letters = string.ascii_uppercase

        try:
            response = await self._client.chat.completions.create(
                model=self.config.stance_selector_model,
                max_tokens=800,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": _SELECTOR_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            _SELECTOR_USER_TEMPLATE
                            .replace("{n}", str(fork_count))
                            .replace("{q}", prompt)
                        ),
                    },
                ],
            )

            raw = response.choices[0].message.content or ""
            stances = self._parse(raw, fork_count, letters)
            return stances

        except Exception:
            # Any error → fall back to built-in stances silently
            return self._fallback(fork_count, letters)

    def _parse(
        self,
        raw: str,
        fork_count: int,
        letters: str,
    ) -> list[SelectedStance]:
        """Parse the AI JSON response into SelectedStance objects.

        Handles common issues like markdown code fences (```json ... ```).
        Falls back to built-in stances on any parse failure.
        """
        text = raw.strip()

        # Strip markdown code fences: ```json\n...\n``` or ```\n...\n```
        if text.startswith("```"):
            # Remove first line (```json or ```) and last fence (```)
            lines = text.split("\n")
            # Drop first line (the opening fence)
            lines = lines[1:]
            # Drop last line if it's a closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Find the JSON array boundaries
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            return self._fallback(fork_count, letters)

        try:
            data = json.loads(text[start:end])
        except json.JSONDecodeError:
            return self._fallback(fork_count, letters)

        if not isinstance(data, list) or len(data) == 0:
            return self._fallback(fork_count, letters)

        stances: list[SelectedStance] = []
        for i, item in enumerate(data[:fork_count]):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", f"perspective-{i+1}")).strip()
            description = str(item.get("description", "")).strip()
            system_prompt = str(item.get("system_prompt", "")).strip()

            if not name or not system_prompt:
                continue

            stances.append(SelectedStance(
                id=letters[i] if i < len(letters) else str(i),
                name=name,
                description=description,
                system_prompt=system_prompt,
            ))

        if len(stances) < 2:
            return self._fallback(fork_count, letters)

        # Pad to fork_count if AI returned fewer than requested
        while len(stances) < fork_count:
            fallback_list = self._fallback(fork_count, letters)
            extra = fallback_list[len(stances)]
            stances.append(extra)

        return stances[:fork_count]

    def _fallback(self, fork_count: int, letters: str) -> list[SelectedStance]:
        """Return built-in stances when dynamic selection fails."""
        builtin_names = list(BUILT_IN_STANCES.keys())
        result = []
        for i in range(fork_count):
            name = builtin_names[i % len(builtin_names)]
            result.append(SelectedStance(
                id=letters[i] if i < len(letters) else str(i),
                name=name,
                description=f"Reasoning from a {name} perspective.",
                system_prompt=BUILT_IN_STANCES[name],
            ))
        return result

    def to_forks(self, stances: list[SelectedStance]) -> list[Fork]:
        """Convert a list of SelectedStance to Fork objects ready for execution."""
        return [
            Fork(
                id=s.id,
                stance=s.name,
                system_prompt=s.system_prompt,
            )
            for s in stances
        ]
