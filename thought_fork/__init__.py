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
Thought Fork — Branch your AI's reasoning like Git branches.

Thought Fork spawns N parallel reasoning paths ("forks") from a single prompt,
each biased by a different stance, then merges them into a synthesis with
explicit attribution.

Concept and vocabulary by Ameen Saeed, June 2026.

Quick usage::

    from thought_fork import ForkManager, SynthesisEngine

    manager = ForkManager()
    forks = await manager.create_forks("Your question here")
    forks = await manager.run_parallel(forks, "Your question here")

    engine = SynthesisEngine()
    synthesis, tokens, duration = await engine.synthesize("Your question here", forks)
"""

__version__ = "0.1.0"
__author__ = "Ameen Saeed"

from thought_fork.config import BUILT_IN_STANCES, ForkConfig
from thought_fork.fork import Fork, get_stance_prompt
from thought_fork.manager import ForkManager
from thought_fork.synthesis import SynthesisEngine

__all__ = [
    "Fork",
    "ForkConfig",
    "ForkManager",
    "SynthesisEngine",
    "BUILT_IN_STANCES",
    "get_stance_prompt",
]
