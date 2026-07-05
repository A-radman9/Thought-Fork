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
Thought Fork — Dynamic Stance Selector.

The StanceSelector reads a user's prompt and uses a fast AI call to
invent the N most insightful and complementary reasoning perspectives
for that specific question. Each perspective gets a custom name,
description, and system prompt — all tailored to the prompt.

This is the core of the "Dynamic Stance Selection" feature introduced
in v0.5.0. It replaces the static built-in stance list with AI-generated
perspectives that are unique to every question asked.

Concept by Thought Fork Contributors, June 2026.
"""

from __future__ import annotations

import json
import logging
import os
import string
from dataclasses import dataclass

from openai import AsyncOpenAI

from thought_fork.config import BUILT_IN_STANCES, ForkConfig
from thought_fork.fork import Fork
from thought_fork.message import Message

logger = logging.getLogger("thought_fork.stance_selector")


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
    assigned_model: str = "default"


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_SELECTOR_SYSTEM = (
    "You are a world-class reasoning architect for the Thought Fork AI framework. "
    "Your job is to analyze a user's question and design the most powerful, "
    "distinct, and complementary expert reasoning perspectives to examine it from. "
    "Each perspective must represent a genuinely different intellectual discipline, "
    "domain expertise, or cognitive strategy — not surface-level rephrases. "
    "Think like you're assembling a dream team of the world's best experts for a war room. "
    "Be highly specific and domain-aware. Avoid generic names like 'balanced', 'general', or 'analyst'. "
    "Return ONLY a valid JSON object. No explanation, no markdown, no prose. Just raw JSON."
)

_DEEPEN_SELECTOR_SYSTEM = (
    "You are an adversarial reasoning architect for the Thought Fork AI framework. "
    "Your job is to ruthlessly dissect the PREVIOUS SYNTHESIS: find every shallow assumption, "
    "every unresolved contradiction, every gap in evidence, every logical leap, "
    "and every perspective that was missing entirely. "
    "Then, invent exactly {n} hyper-specialized expert perspectives designed to "
    "surgically attack those specific weaknesses and force the analysis to a much deeper level. "
    "These stances should feel like bringing in specialist consultants to challenge the first team's conclusions. "
    "Return ONLY a valid JSON object. No explanation, no markdown. Just raw JSON."
)

_SELECTOR_USER_TEMPLATE = (
    "Design {n} expert reasoning perspectives for this question.\n\n"
    "{manual_instruction}\n"
    "{models_instruction}\n"
    "Question: {q}\n\n"
    "Return a JSON object containing a single key 'stances' which is an array of {n} objects. Each object must have:\n"
    '- "name": short kebab-case label that sounds like a real expert role (e.g. "adversarial-red-teamer", "behavioral-economist", "systems-architect")\n'
    '- "description": one vivid sentence explaining what makes this perspective uniquely valuable for THIS specific question\n'
    '- "system_prompt": A DETAILED 5-8 sentence expert briefing. Include: (1) who you are and your domain expertise, '
    '(2) your intellectual methodology and cognitive biases you deliberately employ, '
    '(3) the specific lens through which you analyze this type of problem, '
    '(4) what you prioritize and what you deliberately challenge, '
    '(5) the depth and rigor expected in your analysis. '
    'Write it as if briefing a senior consultant before a high-stakes advisory session. '
    'The system prompt MUST push the AI to produce deep, expert-level, thoroughly reasoned responses — NOT surface-level summaries.\n'
    '- "assigned_model": {model_assignment_rules}'
)

_DEEPEN_USER_TEMPLATE = (
    "Design {n} adversarial reasoning perspectives to critique and deepen this analysis.\n\n"
    "{models_instruction}\n"
    "Original Question: {q}\n\n"
    "--- PREVIOUS SYNTHESIS ---\n"
    "{initial_synthesis}\n"
    "--------------------------\n\n"
    "Return a JSON object containing a single key 'stances' which is an array of {n} objects. Each object must have:\n"
    '- "name": short kebab-case label that sounds like a real expert role (e.g. "adversarial-red-teamer", "behavioral-economist", "systems-architect")\n'
    '- "description": one vivid sentence explaining what makes this perspective uniquely valuable for critiquing the previous synthesis\n'
    '- "system_prompt": A DETAILED 5-8 sentence expert briefing. Include: (1) who you are and your domain expertise, '
    '(2) your intellectual methodology and cognitive biases you deliberately employ, '
    '(3) the specific lens through which you analyze this type of problem, '
    '(4) what you prioritize and what you deliberately challenge, '
    '(5) the depth and rigor expected in your analysis. '
    'Write it as if briefing a senior consultant before a high-stakes advisory session. '
    'The system prompt MUST push the AI to produce deep, expert-level, thoroughly reasoned responses — NOT surface-level summaries.\n'
    '- "assigned_model": {model_assignment_rules}'
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
        
        if self.config.client:
            self._client = self.config.client
        else:
            self._client = AsyncOpenAI(
                base_url=self.config.api_base_url,
                api_key=self.config.api_key,
            )

    async def select(
        self,
        prompt: str,
        fork_count: int | str = 3,
        history: list[Message] | None = None,
        manual_stances: list[str] | None = None,
        initial_synthesis: str | None = None,
    ) -> list[SelectedStance]:
        """Select dynamic stances for a given prompt.

        Args:
            prompt: The user's question to analyze.
            fork_count: Number of stances to select.
            history: Previous messages in the session.
            manual_stances: List of stances explicitly requested by the user.
            initial_synthesis: If provided, runs in 'deepen' mode to critique this synthesis.

        Returns:
            A list of SelectedStance objects — one per fork.
        """
        letters = string.ascii_uppercase
        
        is_auto = fork_count == "auto" or fork_count == "Auto"
        n_phrase = "between 1 and 6 (CRITICAL: use exactly 1 for simple/factual questions, 2-3 for moderate questions, and only use 4-6 for genuinely complex, multi-faceted problems)" if is_auto else f"exactly {fork_count}"
        
        # Determine systems prompt
        sys_prompt = _DEEPEN_SELECTOR_SYSTEM.replace("exactly {n}", n_phrase) if initial_synthesis else _SELECTOR_SYSTEM.replace("exactly {n}", n_phrase)
        
        # Format manual stances instruction
        manual_instruction = ""
        if manual_stances:
            manual_instruction = f"The user has EXPLICITLY REQUESTED the following stances: {', '.join(manual_stances)}. You MUST include these as part of your stances and generate system prompts for them. Invent the remaining stances yourself to reach the requested total."

        models_instruction = ""
        model_assignment_rules = 'always output "default"'
        if self.config.available_models:
            models_list = ", ".join(self.config.available_models)
            models_instruction = f"AVAILABLE AI MODELS: {models_list}\n"
            model_assignment_rules = f'select the exact model string from the available models list that best fits this stance\'s expertise. If unsure, use "default"'

        try:
            messages = [{"role": "system", "content": sys_prompt}]
            if history:
                messages.extend(history)
            
            if initial_synthesis:
                user_msg = (
                    _DEEPEN_USER_TEMPLATE
                    .replace("{n}", n_phrase)
                    .replace("{models_instruction}", models_instruction)
                    .replace("{model_assignment_rules}", model_assignment_rules)
                    .replace("{initial_synthesis}", initial_synthesis)
                    .replace("{q}", prompt)
                )
            else:
                user_msg = (
                    _SELECTOR_USER_TEMPLATE
                    .replace("{n}", n_phrase)
                    .replace("{manual_instruction}", manual_instruction)
                    .replace("{models_instruction}", models_instruction)
                    .replace("{model_assignment_rules}", model_assignment_rules)
                    .replace("{q}", prompt)
                )
            
            messages.append({
                "role": "user",
                "content": user_msg,
            })
            
            response = await self._client.chat.completions.create(
                model=self.config.stance_selector_model,
                max_tokens=2000,
                temperature=0.7,
                messages=messages,
            )

            raw = response.choices[0].message.content or ""
            parsed_limit = 6 if is_auto else (int(fork_count) if isinstance(fork_count, (int, str)) and str(fork_count).isdigit() else 3)
            stances = self._parse(raw, parsed_limit, letters, is_auto=is_auto)
            
            # Fallback guarantee: if manual stances are completely ignored by the AI,
            # we should forcefully include them (though the AI usually complies).
            if manual_stances:
                returned_names = [s.name.lower() for s in stances]
                for i, ms in enumerate(manual_stances):
                    if not any(ms.lower() in rn or rn in ms.lower() for rn in returned_names):
                        if i < len(stances):
                            stances[i] = SelectedStance(
                                id=letters[i] if i < len(letters) else str(i),
                                name=ms.replace(" ", "-").lower(),
                                description=f"Reasoning from a {ms} perspective.",
                                system_prompt=f"You are reasoning from the perspective of: {ms}.",
                            )

            return stances

        except Exception as e:
            # Any error → fall back to built-in stances silently
            logger.warning(f"Dynamic stance selection failed: {e}. Falling back to built-in stances.")
            return self._fallback(fork_count, letters)

    def _parse(
        self,
        raw: str,
        fork_count: int,
        letters: str,
        is_auto: bool = False,
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

        # Find the JSON object boundaries
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            logger.warning("Could not find JSON object bounds in dynamic stance response.")
            return self._fallback(fork_count, letters)

        try:
            data = json.loads(text[start:end])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse dynamic stance JSON: {e}")
            return self._fallback(fork_count, letters)

        if not isinstance(data, dict) or "stances" not in data or not isinstance(data["stances"], list):
            # Sometimes models ignore the 'stances' wrapper, check if it's a list directly
            if isinstance(data, list):
                stances_data = data
            else:
                logger.warning("Dynamic stance response missing 'stances' array.")
                return self._fallback(fork_count, letters)
        else:
            stances_data = data["stances"]

        stances: list[SelectedStance] = []
        for i, item in enumerate(stances_data[:fork_count]):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", f"perspective-{i+1}")).strip()
            description = str(item.get("description", "")).strip()
            system_prompt = str(item.get("system_prompt", "")).strip()
            assigned_model = str(item.get("assigned_model", "default")).strip()

            if not name or not system_prompt:
                continue

            stances.append(SelectedStance(
                id=letters[i] if i < len(letters) else str(i),
                name=name,
                description=description,
                system_prompt=system_prompt,
                assigned_model=assigned_model,
            ))

        if len(stances) < 2:
            return self._fallback(fork_count, letters)

        # In auto mode, we don't force padding unless it's < 2
        # If not auto, pad to fork_count
        if not is_auto and fork_count and len(stances) < fork_count:
            while len(stances) < fork_count:
                fallback_list = self._fallback(fork_count, letters)
                extra = fallback_list[len(stances) % len(fallback_list)]
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
