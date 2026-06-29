# Thought Fork — Complete Build Plan

> **The term you're coining:** Thought Fork — branch your AI's reasoning like Git branches.
> Build this phase by phase. Each phase has a ready-to-use brief for your AI coding tool.

---

## What Is Thought Fork

Traditional AI gives you one answer from one reasoning path. Thought Fork spawns N parallel "forks" from the same prompt, each reasoning from a different stance, then a synthesis step merges them into a final answer that explicitly attributes what came from where.

The vocabulary you're establishing:
- **Fork** — a single parallel reasoning path
- **Forking** — the act of spawning parallel paths from one prompt
- **Stance** — the reasoning angle a fork takes (cautious, creative, critical)
- **Convergence** — the synthesis step where all forks merge
- **Fork depth** — how many levels of branching occurred

---

## Architecture Overview

```
User Prompt
     │
     ▼
ForkManager
     │
     ├──► Fork A (cautious)   → reasoning chain A
     ├──► Fork B (creative)   → reasoning chain B
     └──► Fork C (critical)   → reasoning chain C
                │
                ▼
        SynthesisEngine
                │
                ▼
     Final Answer
     "From Fork A's risk analysis...
      Fork B surfaced an angle...
      Fork C challenged the assumption..."
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Core logic | Python 3.11+ | Best AI tooling ecosystem |
| AI API | Anthropic Claude API | Haiku for forks, Sonnet for synthesis |
| Backend | FastAPI + asyncio | Streaming + parallel execution |
| Frontend | React + Tailwind CSS | Component-based, fast to build |
| Storage | SQLite | Simple session persistence |
| Package | Poetry | Clean PyPI packaging |

**Token efficiency built in by design:**
- Forks run on `claude-haiku` (fast, cheap, parallel)
- Synthesis runs on `claude-sonnet` (quality where it counts)
- Optional: swap haiku for local Ollama models (zero API cost)

---

## Phase 1 — The Fork Engine
### Pure Python. No UI. No API. Prove the concept.

**Goal:** A script you run from the terminal. Give it a prompt, watch 3 forks think in parallel, see a synthesis.

**Folder structure to create:**
```
thought-fork/
├── thought_fork/
│   ├── __init__.py
│   ├── fork.py          ← Fork dataclass + stance definitions
│   ├── manager.py       ← ForkManager: spawns + runs forks in parallel
│   ├── synthesis.py     ← SynthesisEngine: merges fork outputs
│   └── config.py        ← ForkConfig: models, default stances, fork count
├── examples/
│   └── basic_fork.py    ← Your first working demo
├── .env                 ← ANTHROPIC_API_KEY=...
└── requirements.txt
```

**Core logic to implement:**

`fork.py` — Fork dataclass:
```python
@dataclass
class Fork:
    id: str                  # "A", "B", "C"
    stance: str              # "cautious", "creative", "critical"
    system_prompt: str       # the stance instruction
    output: str = ""
    token_count: int = 0
    duration_ms: int = 0
```

`manager.py` — ForkManager:
```python
async def create_forks(prompt, stances=["cautious","creative","critical"]) -> list[Fork]
async def run_parallel(forks) -> list[Fork]   # asyncio.gather() all forks
```

`synthesis.py` — SynthesisEngine:
```python
async def synthesize(prompt, forks) -> str
# Prompt: "Here are N reasoning paths for the question: [prompt]
#  Fork A (cautious): [output A]
#  Fork B (creative): [output B]
#  Fork C (critical): [output C]
#  Synthesize these into a final answer, explicitly crediting each fork."
```

**Built-in stances:**

| Stance | System prompt |
|--------|--------------|
| cautious | Reason carefully. Identify risks, edge cases, and failure modes. |
| creative | Think laterally. Explore unconventional and non-obvious angles. |
| critical | Challenge every assumption. Play devil's advocate. Find weaknesses. |
| pragmatic | Focus only on what is practical and immediately actionable. |
| first-principles | Break everything down to fundamentals. Ignore conventional wisdom. |

---

### Phase 1 Brief — copy this into your AI coding tool:

```
Build the core logic for a Python library called "thought-fork".

Concept: A ForkManager spawns N parallel AI reasoning paths ("forks") from 
a single user prompt. Each fork has a different "stance" (cautious, creative, 
critical) that biases its reasoning via its system prompt. All forks run 
concurrently using asyncio + the Anthropic Claude API. A SynthesisEngine 
then merges all fork outputs into a final answer that explicitly says which 
fork contributed what.

Use claude-haiku-3-5 for forks (fast and cheap) and claude-sonnet-4-6 for 
synthesis (quality where it matters). Store the API key in a .env file.

Files to create:
- thought_fork/fork.py — Fork dataclass: id, stance, system_prompt, output, 
  token_count, duration_ms
- thought_fork/manager.py — ForkManager with create_forks(prompt, stances) 
  and run_parallel(forks) using asyncio.gather()
- thought_fork/synthesis.py — SynthesisEngine with synthesize(prompt, forks) 
  that sends all fork outputs to Claude with explicit attribution instructions
- thought_fork/config.py — ForkConfig dataclass: fork_model, synthesis_model, 
  default_stances list, max_tokens
- examples/basic_fork.py — Demo that forks the question "Should I build a 
  monolith or microservices?" with 3 stances and prints results with attribution

No UI. Terminal output only. Log token count and duration per fork.
Print results with clear fork labels: === Fork A (cautious) === etc.
```

**Done when:**
- [ ] `python examples/basic_fork.py` runs and prints 3 different reasoning paths
- [ ] The synthesis output explicitly mentions "From the cautious fork..." or similar
- [ ] Token count is printed per fork at the end
- [ ] The three forks run concurrently (not one after another)

---

## Phase 2 — The API Layer
### Turn the core into a streaming REST API.

**Goal:** A FastAPI server at `localhost:8000`. POST a prompt, get streaming fork outputs back as Server-Sent Events.

**New files to create:**
```
thought-fork/
├── api/
│   ├── main.py          ← FastAPI app + CORS
│   ├── routes/
│   │   └── fork.py      ← POST /fork endpoint
│   ├── models.py        ← Pydantic request/response models
│   └── streaming.py     ← SSE event builder helper
└── api_requirements.txt
```

**Streaming event shape** (what the frontend will receive):
```json
{"fork_id": "A", "stance": "cautious", "chunk": "Let me consider the risks...", "is_done": false}
{"fork_id": "B", "stance": "creative", "chunk": "What if we approached...", "is_done": false}
{"fork_id": "synthesis", "stance": null, "chunk": "Drawing from Fork A...", "is_done": false}
{"fork_id": "synthesis", "stance": null, "chunk": "", "is_done": true, "session_id": "abc123"}
```

All forks stream interleaved — Fork A and Fork B emit chunks at the same time. Do not wait for one to finish before starting another.

**Endpoints:**
- `POST /fork` — body: `{prompt, fork_count, stances}` → SSE stream
- `GET /forks/{session_id}` — retrieve a past fork session
- `GET /health` — health check

**SQLite sessions table:**
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  prompt TEXT,
  created_at TIMESTAMP,
  fork_outputs JSON,
  synthesis_output TEXT,
  total_tokens INTEGER
);
```

---

### Phase 2 Brief — copy this into your AI coding tool:

```
Add a FastAPI streaming API to the thought-fork library. The core logic 
already exists in thought_fork/ — just wrap it in an API.

Create api/main.py with FastAPI. Add CORS for localhost:3000.

Main endpoint: POST /fork
- Accepts: {prompt: str, fork_count: int = 3, stances: list[str]}
- Returns: Server-Sent Events stream
- Each SSE event is JSON: {fork_id, stance, chunk, is_done, session_id?}
- Forks stream in parallel — interleave chunks from Fork A and B simultaneously
- After all forks complete, stream the synthesis with fork_id="synthesis"
- On synthesis completion, include session_id in the final is_done event

Also create:
- GET /forks/{session_id} to retrieve saved sessions
- GET /health for basic health check
- SQLite persistence: save each session (prompt, fork_outputs, synthesis)
- api/models.py with Pydantic ForkRequest and ForkEvent models

Run with: uvicorn api.main:app --reload --port 8000
```

**Done when:**
- [ ] Server starts: `uvicorn api.main:app --reload`
- [ ] curl test shows interleaved streaming chunks from Fork A and B simultaneously
- [ ] SQLite file is created and sessions are saved
- [ ] `GET /forks/{session_id}` returns the stored session

---

## Phase 3 — The Visual Demo
### The shareable moment. This is what makes the term spread.

**Goal:** A web app at `localhost:3000`. Type a prompt, watch 3 thought forks branch out live, watch them converge. Record this as your demo video.

**Folder structure:**
```
thought-fork-ui/
├── src/
│   ├── App.jsx
│   ├── components/
│   │   ├── PromptInput.jsx       ← Prompt textarea + fork config + Fork button
│   │   ├── ForkPanel.jsx         ← Single fork: stance badge + streaming text
│   │   ├── ForkGrid.jsx          ← 3 ForkPanels side by side
│   │   └── SynthesisPanel.jsx    ← Synthesis output with fade-in
│   ├── hooks/
│   │   └── useForkStream.js      ← EventSource SSE hook
│   └── main.jsx
├── package.json
└── index.html
```

**UI layout:**
```
┌──────────────────────────────────────────────────────┐
│  What do you want to fork?                           │
│  [Should I use microservices or a monolith?    ][▶ Fork] │
└──────────────────────────────────────────────────────┘

    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │🔵 Cautious│    │🟡 Creative│    │🔴 Critical│
    │           │    │           │    │           │
    │ Let me    │    │ What if   │    │ I want to │
    │ consider  │    │ we looked │    │ challenge │
    │ the risks │    │ at this   │    │ the core  │
    │ here...   │    │ from a    │    │ assumption│
    │           │    │ different │    │ here...   │
    └──────────┘    └──────────┘    └──────────┘
                         │
              ┌──────────────────────┐
              │  ✦ Synthesis          │
              │                      │
              │  Drawing from the    │
              │  cautious fork's     │
              │  risk analysis and   │
              │  the creative fork's │
              │  alternative view... │
              └──────────────────────┘
```

**Visual details that make it shareable:**
- Fork A = blue, Fork B = amber, Fork C = teal (consistent color identity)
- Forks animate in with fade + slide-up when they start streaming
- Synthesis panel fades in only after all forks emit their final chunk
- Stance badge on each panel (colored pill: "Cautious", "Creative", "Critical")
- Token count shown as a small badge on each fork when complete
- "Copy synthesis" button on the synthesis panel
- "New Fork" button resets everything

---

### Phase 3 Brief — copy this into your AI coding tool:

```
Build a React + Tailwind CSS frontend for "Thought Fork" — an AI reasoning 
visualization app that connects to a FastAPI backend at localhost:8000.

User flow:
1. User types a prompt and clicks "Fork"
2. App calls POST localhost:8000/fork with SSE streaming via EventSource
3. Three fork panels appear simultaneously, each streaming their reasoning
4. Each fork has a color: blue=cautious, amber=creative, teal=critical
5. After all forks complete, a synthesis panel fades in below

Components:
- PromptInput: textarea (full width), Fork button, fork count selector (2-5)
- ForkPanel: stance badge (colored pill), streaming text, token count badge 
  when done. Animates in with fade+slideUp when it starts receiving data.
- ForkGrid: renders 3 ForkPanels side by side (responsive: stack on mobile)
- SynthesisPanel: "✦ Synthesis" header, streaming text, Copy button. 
  Only renders after all forks complete their streaming.

State: idle → forking → synthesizing → complete → idle

Use the native EventSource API for SSE from localhost:8000/fork.
Dark theme. Clean, minimal. Monospace font for fork output text.
"New Fork" button resets state back to idle.

No auth, no backend calls beyond the fork endpoint.
```

**Done when:**
- [ ] Three fork panels stream simultaneously with different colors
- [ ] Synthesis fades in after all forks complete
- [ ] The 30-second screen recording looks impressive enough to share
- [ ] Responsive on mobile (panels stack vertically)

---

## Phase 4 — The Installable Package
### Make it something other developers can actually use in their projects.

**Goal:** `pip install thought-fork` works. Other developers can import it in 3 lines.

**Changes needed:**
```
thought-fork/
├── pyproject.toml          ← Poetry config, package metadata
├── README.md               ← This IS the manifesto
├── thought_fork/
│   ├── __init__.py         ← Clean public API exports
│   └── ...existing files (no changes)
├── examples/
│   ├── basic_fork.py       ← existing
│   ├── code_review.py      ← Fork a code review
│   ├── decision_making.py  ← Fork a business decision
│   └── research.py         ← Fork a research question
└── tests/
    ├── test_fork.py
    └── test_synthesis.py
```

**The clean public API** (what developers will write):
```python
# Simple — one function call
from thought_fork import synthesize

result = await synthesize(
    "Should I migrate to microservices?",
    fork_count=3
)

print(result.synthesis)           # Final merged answer
print(result.forks["cautious"])   # Individual fork output
print(result.token_usage)         # {"forks": 1240, "synthesis": 380, "total": 1620}

# Advanced — custom stances
from thought_fork import Fork, synthesize

result = await synthesize(
    "Review this architecture",
    forks=[
        Fork(stance="security",     system_prompt="Find vulnerabilities"),
        Fork(stance="performance",  system_prompt="Find bottlenecks"),
        Fork(stance="maintainability", system_prompt="Find complexity risks"),
    ]
)
```

---

### Phase 4 Brief — copy this into your AI coding tool:

```
Polish the thought-fork Python library for PyPI publication.

1. Create pyproject.toml with Poetry:
   name="thought-fork", version="0.1.0"
   description="Branch AI reasoning into parallel thought paths"
   Dependencies: anthropic, fastapi, python-dotenv, aiohttp

2. Update thought_fork/__init__.py to export a clean public API:
   - synthesize() as the main async entry point
   - Fork, ForkManager, ForkResult, ForkConfig as importable classes

3. Create ForkResult dataclass:
   synthesis: str
   forks: dict[str, str]    # stance → output
   token_usage: dict        # forks, synthesis, total
   duration_ms: int

4. Add 3 example files in examples/:
   - code_review.py: fork a code review with security/performance/maintainability stances
   - decision_making.py: fork "Should I quit my job and freelance?"
   - research.py: fork a technical research question

5. Write basic pytest tests:
   - test_fork.py: test Fork creation, stance assignment, system_prompt generation
   - test_synthesis.py: test ForkResult structure, test attribution in synthesis

6. Write README.md with:
   - One-line definition
   - Install instructions  
   - Quickstart (5 lines of code)
   - Example output showing 3 forks + synthesis
   - Available stances table
   - "The concept" section explaining why single-path reasoning is limiting
```

**Done when:**
- [ ] `pip install -e .` works locally
- [ ] `from thought_fork import synthesize` works in a fresh file
- [ ] All 3 example files run without errors
- [ ] Tests pass with `pytest`

---

## Phase 5 — Launch
### Make "Thought Fork" the term people use. Not a product — a concept.

This phase is not code. It's how a GitHub repo becomes a term.

---

### The GitHub Repository

**Repo name:** `thought-fork` (not `thought-fork-py` or `thoughtfork-ai`)

**README structure** — write this before the documentation:
1. One-line: *"Thought Fork: branch your AI's reasoning like Git branches."*
2. The visual (screenshot of UI with 3 forks streaming)
3. Quickstart (10 lines)
4. The concept (why single-path reasoning limits AI quality)
5. Available stances
6. How to add custom stances
7. Contributing

The README is the manifesto. Someone who's never used the tool should understand the concept from the README alone.

---

### The Concept Post

**Title:** *"I got tired of AI giving me one answer. So I taught it to fork."*

**Structure:**
1. The frustration (a real example: you asked AI something important, got one answer, it was wrong in a way a second opinion would have caught)
2. The insight (reasoning should branch, not chain)
3. The demo (embedded gif or video showing forks streaming)
4. The vocabulary: fork, stance, convergence, synthesis — explain each
5. Quickstart code block
6. Call to action: "What would you fork?" + GitHub link

**Where to publish:** dev.to first → cross-post Hashnode → Medium.
**Where to share:** X/Twitter, LinkedIn, Reddit r/MachineLearning + r/LocalLLaMA + r/Python.

---

### The Demo Video

**30-45 seconds. No voiceover. Just the screen.**

Script:
1. Open the UI (already at localhost:3000 with a clean state)
2. Type: *"Should I quit my job and start a startup?"*
3. Click Fork — let it run
4. Show the 3 forks streaming simultaneously
5. Watch synthesis emerge
6. Hold on the synthesis for 3 seconds
7. Cut to black: *"Thought Fork — branch your AI's reasoning"*
8. GitHub link on screen

Record with Loom, OBS, or QuickTime. Post on X, LinkedIn, YouTube Shorts.
The video is more important than the blog post.

---

### Vocabulary to seed in everything you write

When people start using these words without thinking, you've coined the term:

| Word | Usage |
|------|-------|
| to fork | "I forked the question into 3 stances" |
| fork depth | "Try fork depth 2 for harder problems" |
| fork convergence | "The convergence synthesized something the individual forks missed" |
| fork stance | "What stance did you use?" |
| thought branch | "The creative branch caught something the others didn't" |

---

## Timeline

| Phase | Deliverable | Estimated time |
|-------|------------|----------------|
| Phase 1 | Core engine — terminal demo | 1–2 days |
| Phase 2 | API layer — streaming endpoints | 1 day |
| Phase 3 | Visual demo — shareable UI | 2–3 days |
| Phase 4 | Installable package | 1–2 days |
| Phase 5 | Launch materials | Ongoing |

**First shareable demo: approximately 1 week from starting Phase 1.**

---

## Appendix A — Built-in Stances Reference

| Stance | System prompt | Best for |
|--------|--------------|----------|
| cautious | Reason carefully. Identify risks, edge cases, and failure modes first. | Architecture decisions, security reviews |
| creative | Think laterally. Explore unconventional and non-obvious angles. | Brainstorming, design problems |
| critical | Challenge every assumption. Play devil's advocate. Find the weaknesses. | Code review, business plans |
| pragmatic | Focus only on what is immediately practical and resource-efficient. | Planning, implementation |
| first-principles | Break everything down to fundamentals. Ignore conventional wisdom. | Complex problems, new domains |
| optimistic | Identify best-case outcomes and the path to achieve them. | Strategy, motivation |
| contrarian | Argue the opposite of the obvious answer. | Challenging groupthink |

---

## Appendix B — Token Efficiency Strategy

This maps to the "burning fewer tokens" interest:

| Component | Model | Reason |
|-----------|-------|--------|
| Forks (default) | claude-haiku-3-5 | Fast, cheap, runs 3 in parallel |
| Synthesis | claude-sonnet-4-6 | Quality matters here |
| Forks (local option) | Ollama phi-3 / gemma | Zero API cost |
| Cached forks | Skip API call | Same prompt+stance → reuse stored output |

Estimated cost per fork session (3 forks + synthesis):
- Haiku forks: ~$0.002 total
- Sonnet synthesis: ~$0.005
- Total per session: ~$0.007

---

## Appendix C — Context Passport (Phase 6 — Future)

Once you have an audience from Thought Fork, this is your next term.

Context Passport solves the problem of AI context being trapped in silos. When you switch from ChatGPT to Claude to Cursor, everything resets. A Context Passport is a portable, open-format representation of your AI context that any tool can import and export.

You can't define an open standard when you're unknown. Thought Fork builds the reputation. Context Passport is what you announce once that audience exists. Keep it in mind as the bigger vision, but don't split focus now.

---

*Start with Phase 1. The entire plan depends on Phase 1 being real.*
