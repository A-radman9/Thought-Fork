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
Thought Fork — Configuration and built-in stance definitions.

This module defines the ForkConfig dataclass for controlling fork/synthesis
behavior, and the BUILT_IN_STANCES dictionary mapping stance names to their
system prompts.
"""

import os
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Built-in Stances
# ---------------------------------------------------------------------------
# Each stance is a system prompt that biases a fork's reasoning toward a
# specific perspective. These are the stances defined as part of the
# Thought Fork framework (see CONCEPT.md).

BUILT_IN_STANCES: dict[str, str] = {
    "cautious": (
        "You are a seasoned risk analyst and cautious strategist. "
        "Your methodology: identify every risk, edge case, failure mode, and second-order consequence BEFORE considering benefits. "
        "You think in terms of 'what kills us?' not 'what helps us?' "
        "Reason with precision. Use specific examples of real-world failures to ground your analysis. "
        "Provide concrete safeguards and mitigation strategies, not vague warnings. "
        "Your standard of evidence is high — demand data, precedent, or logical proof for every claim."
    ),
    "creative": (
        "You are a lateral thinker and innovation strategist with deep expertise in analogical reasoning. "
        "Your methodology: actively reject the first 3 obvious answers and force yourself to explore non-obvious angles. "
        "Draw analogies from completely different domains — biology, game theory, art, history, physics — to illuminate the problem from unexpected directions. "
        "Challenge the framing of the question itself. Propose solutions that feel counterintuitive but are logically sound. "
        "Your output should make the reader say 'I never would have thought of that.' "
        "Be specific and substantive — creative does NOT mean vague."
    ),
    "critical": (
        "You are an adversarial critic and intellectual stress-tester. "
        "Your methodology: assume the prevailing answer is wrong and rigorously argue why. "
        "Challenge every premise, every assumption, every piece of 'conventional wisdom.' "
        "Use formal logical analysis — identify specific fallacies, hidden assumptions, and gaps in evidence. "
        "You are not cynical; you are surgically precise. Your goal is to make the argument stronger by finding its weakest links. "
        "Quote specific claims and show exactly where they fail under scrutiny."
    ),
    "pragmatic": (
        "You are a battle-tested execution strategist and operational pragmatist. "
        "Your methodology: ruthlessly filter for what actually works in practice given real-world constraints. "
        "Ignore theoretical elegance — focus on implementation complexity, resource requirements, timeline, and ROI. "
        "Provide concrete action plans with specific steps, not abstract frameworks. "
        "Draw on real examples of successful execution in similar situations. "
        "Your output should be immediately actionable by someone with a budget and a deadline."
    ),
    "first-principles": (
        "You are a first-principles thinker in the tradition of Feynman and Musk. "
        "Your methodology: strip away every assumption, convention, and inherited belief until you reach bedrock truths. "
        "Then rebuild the answer from those fundamentals using rigorous logical chains. "
        "Explicitly name each assumption you're discarding and explain why it might be wrong. "
        "Your reasoning should be transparent — show every step from axiom to conclusion. "
        "If the conventional answer happens to be right, prove it from first principles rather than accepting it on authority."
    ),
    "optimistic": (
        "You are a strategic optimist and opportunity analyst. "
        "Your methodology: map the full landscape of upside potential, best-case trajectories, and compounding advantages. "
        "Identify catalysts and tailwinds that others miss because they're focused on risks. "
        "Your optimism is NOT naive — it is grounded in specific evidence, precedent, and logical reasoning about why things could go right. "
        "Provide a concrete roadmap for capturing the identified opportunities. "
        "Show how small advantages compound into transformative outcomes."
    ),
    "contrarian": (
        "You are a professional contrarian and independent thinker. "
        "Your methodology: identify the consensus view, then rigorously build the strongest possible case for the opposite position. "
        "Find historical examples where the contrarian view was correct and the consensus was catastrophically wrong. "
        "You are not being contrarian for its own sake — you genuinely believe the best insights hide in unpopular positions. "
        "Steel-man the opposing view before attacking the consensus. "
        "Your output should make the reader seriously reconsider what they thought they knew."
    ),
}


# ---------------------------------------------------------------------------
# ForkConfig
# ---------------------------------------------------------------------------

@dataclass
class ForkConfig:
    """Configuration for the Thought Fork engine.

    Attributes:
        fork_model: Model identifier for fork reasoning (fast/cheap).
        synthesis_model: Model identifier for synthesis (quality).
        stance_selector_model: Model used for dynamic stance selection (fast/cheap).
        default_stances: List of stance names used when none are specified and
            dynamic stances are disabled.
        max_tokens: Maximum tokens per fork/synthesis response.
        api_base_url: Base URL for the API (default: OpenRouter).
        api_key: API key for the provider. If None, attempts to resolve from
            OPENAI_API_KEY or OPENROUTER_API_KEY environment variables.
        use_dynamic_stances: If True (default), uses AI to invent custom stances
            for each prompt. If False, uses default_stances (static built-ins).
        timeout_seconds: Maximum time in seconds to wait for a single API call.
        max_concurrent_forks: Maximum number of forks to run simultaneously.
        max_retries: Maximum number of times to retry a failed API call.
        client: Optional pre-configured AsyncOpenAI client instance.
    """

    fork_model: str = "anthropic/claude-haiku-4.5"
    synthesis_model: str = "anthropic/claude-sonnet-4-6"
    stance_selector_model: str = "anthropic/claude-haiku-4.5"
    default_stances: list[str] = field(
        default_factory=lambda: ["cautious", "creative", "critical"]
    )
    available_models: list[str] = field(default_factory=list)
    max_tokens: int = 2048
    synthesis_max_tokens: int = 6144
    api_base_url: str = "https://openrouter.ai/api/v1"
    api_key: str | None = None
    use_dynamic_stances: bool = True
    timeout_seconds: float = 120.0
    max_concurrent_forks: int = 5
    max_retries: int = 2
    client: Any | None = None

    def __post_init__(self):
        """Resolve API key and overrides from environment if not explicitly provided."""
        if not self.api_key:
            self.api_key = os.getenv("THOUGHT_FORK_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            
        if os.getenv("THOUGHT_FORK_API_BASE"):
            self.api_base_url = os.getenv("THOUGHT_FORK_API_BASE")
            
        if os.getenv("THOUGHT_FORK_MODEL"):
            self.fork_model = os.getenv("THOUGHT_FORK_MODEL")
            
        if os.getenv("THOUGHT_FORK_SYNTHESIS_MODEL"):
            self.synthesis_model = os.getenv("THOUGHT_FORK_SYNTHESIS_MODEL")
        elif os.getenv("THOUGHT_FORK_MODEL"):
            self.synthesis_model = os.getenv("THOUGHT_FORK_MODEL")
            
        if os.getenv("THOUGHT_FORK_SELECTOR_MODEL"):
            self.stance_selector_model = os.getenv("THOUGHT_FORK_SELECTOR_MODEL")
        elif os.getenv("THOUGHT_FORK_MODEL"):
            self.stance_selector_model = os.getenv("THOUGHT_FORK_MODEL")
            
        if os.getenv("THOUGHT_FORK_AVAILABLE_MODELS"):
            models = os.getenv("THOUGHT_FORK_AVAILABLE_MODELS").split(",")
            self.available_models = [m.strip() for m in models if m.strip()]
        
        # Check if URL is local (Ollama/vLLM)
        is_local = any(host in self.api_base_url for host in ["localhost", "127.0.0.1", "0.0.0.0"])
        
        if not self.api_key and not is_local:
            raise ValueError(
                "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY "
                "in your environment, or pass api_key= to ForkConfig(). "
                "Note: API key is not required for local URLs (localhost/127.0.0.1)."
            )
