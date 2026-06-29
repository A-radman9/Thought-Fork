# 🔀 Thought Fork

**Branch your AI's reasoning like Git branches.**

Thought Fork spawns parallel reasoning paths — each from a different *stance* — then merges them into a single answer that explicitly says which perspective contributed what.

```python
from thought_fork import synthesize

result = await synthesize("Should I migrate to microservices?", fork_count=3)
print(result.synthesis)           # Attributed final answer
print(result.forks["cautious"])   # Individual fork output
print(result.token_usage)         # {"forks": 1240, "synthesis": 380, "total": 1620}
```

---

## How It Works

```
User Prompt
     │
     ▼
ForkManager
     │
     ├──► Fork A (cautious)   → "Let me consider the risks..."
     ├──► Fork B (creative)   → "What if we approached this from..."
     └──► Fork C (critical)   → "I want to challenge the assumption..."
                │
                ▼
        SynthesisEngine
                │
                ▼
     "From the cautious fork's risk analysis...
      The creative fork surfaced an angle...
      The critical fork challenged the assumption..."
```

All forks run **concurrently** via `asyncio`. The synthesis step uses a more capable model to merge outputs with **explicit attribution** — you can see exactly which perspective drove each insight.

---

## Install

```bash
pip install thought-fork
```

With the streaming API server:
```bash
pip install thought-fork[api]
```

---

## Quickstart

```python
import asyncio
from thought_fork import synthesize

async def main():
    result = await synthesize(
        "Should I build a monolith or microservices?",
        fork_count=3,
    )
    
    # The synthesis explicitly credits each fork
    print(result.synthesis)
    
    # Access individual fork reasoning
    for stance, output in result.forks.items():
        print(f"\n--- {stance} ---")
        print(output)
    
    # Token usage
    print(result.token_usage)
    # {"forks": 1155, "synthesis": 661, "total": 1816}

asyncio.run(main())
```

### Custom Stances

```python
from thought_fork import Fork, synthesize

result = await synthesize(
    "Review this architecture",
    forks=[
        Fork(id="A", stance="security",
             system_prompt="Find vulnerabilities and injection risks."),
        Fork(id="B", stance="performance",
             system_prompt="Find bottlenecks and memory issues."),
        Fork(id="C", stance="maintainability",
             system_prompt="Find complexity risks and code smells."),
    ],
)
```

---

## Available Stances

| Stance | What it does | Best for |
|--------|-------------|----------|
| **cautious** | Identifies risks, edge cases, failure modes | Architecture decisions, security reviews |
| **creative** | Explores unconventional, non-obvious angles | Brainstorming, design problems |
| **critical** | Challenges every assumption, plays devil's advocate | Code review, business plans |
| **pragmatic** | Focuses on what's immediately practical | Planning, implementation |
| **first-principles** | Breaks everything down to fundamentals | Complex problems, new domains |
| **optimistic** | Identifies best-case outcomes and paths to achieve them | Strategy, motivation |
| **contrarian** | Argues the opposite of the obvious answer | Challenging groupthink |

You can also define **custom stances** by providing your own system prompt — any perspective you can describe, the fork can reason from.

---

## The Concept

Traditional AI gives you **one answer from one reasoning path**. That answer is shaped by whichever direction the model happened to take first. A different framing might have produced a different — possibly better — answer.

**Thought Fork** solves this by deliberately:

1. **Forking** — spawning multiple reasoning paths from the same prompt
2. **Biasing** — each fork reasons from a different *stance* via its system prompt
3. **Running in parallel** — all forks execute concurrently (wall-clock time ≈ slowest fork)
4. **Converging** — a synthesis step merges all outputs with explicit attribution

The result isn't just "the best answer" — it's an answer that tells you *why* it concluded what it did, and *which perspective* drove each part of the conclusion.

This is analogous to:
- **Git branching** — branch, develop in parallel, merge with a clear diff
- **Ensemble methods in ML** — multiple models, aggregated prediction  
- **Dialectical reasoning** — thesis, antithesis, synthesis

---

## Vocabulary

| Term | Definition |
|------|-----------|
| **Fork** | A single parallel reasoning path |
| **Forking** | Spawning parallel paths from one prompt |
| **Stance** | The reasoning angle a fork takes |
| **Convergence** | The synthesis step where all forks merge |
| **Fork Depth** | How many levels of branching occurred |

---

## API Reference

### `synthesize(prompt, fork_count=3, stances=None, forks=None, config=None)`

The main entry point. Returns a `ForkResult`.

| Param | Type | Description |
|-------|------|-------------|
| `prompt` | `str` | The question to fork |
| `fork_count` | `int` | Number of forks (default: 3) |
| `stances` | `list[str]` | Stance names (default: cautious, creative, critical) |
| `forks` | `list[Fork]` | Advanced: pre-built Fork objects with custom prompts |
| `config` | `ForkConfig` | Override models, token limits, API base URL |

### `ForkResult`

| Field | Type | Description |
|-------|------|-------------|
| `synthesis` | `str` | The merged, attributed answer |
| `forks` | `dict[str, str]` | Stance → output text |
| `fork_details` | `list[dict]` | Full data per fork (id, stance, output, tokens, duration) |
| `token_usage` | `dict` | `{"forks": int, "synthesis": int, "total": int}` |
| `duration_ms` | `int` | Total wall-clock time |

### `ForkConfig`

| Field | Default | Description |
|-------|---------|-------------|
| `fork_model` | `anthropic/claude-haiku-4.5` | Model for forks (fast/cheap) |
| `synthesis_model` | `anthropic/claude-sonnet-4-6` | Model for synthesis (quality) |
| `max_tokens` | `1024` | Max tokens per response |
| `api_base_url` | OpenRouter | API endpoint |

---

## Streaming API

Thought Fork includes an optional FastAPI server for real-time streaming:

```bash
pip install thought-fork[api]
uvicorn api.main:app --port 8000
```

- `POST /fork` — SSE stream with interleaved fork chunks + synthesis
- `GET /forks/{session_id}` — retrieve a stored session
- `GET /health` — health check

---

## Configuration

Set your API key in a `.env` file:

```
OPENROUTER_API_KEY=your-key-here
```

Or use the Anthropic API directly by overriding the config:

```python
from thought_fork import synthesize, ForkConfig

config = ForkConfig(
    api_base_url="https://api.anthropic.com/v1",
    fork_model="claude-3-5-haiku-20241022",
    synthesis_model="claude-sonnet-4-6-20250514",
)
result = await synthesize("Your question", config=config)
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTORS.md](CONTRIBUTORS.md) for guidelines.

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

*Concept and vocabulary by [Ameen Saeed](https://github.com/ameensaeed), June 2026.*
