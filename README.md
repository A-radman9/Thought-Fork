# 🔀 Thought Fork

**Branch your AI's reasoning like Git branches.**

Thought Fork is a Python framework that introduces **Attributed Convergence** to AI reasoning. Instead of asking a single AI model to give you one generic answer, Thought Fork dynamically invents $N$ distinct reasoning perspectives (stances) tailored to your specific prompt, branches the AI into parallel reasoning streams, and then merges them back together into a single, synthesized, highly-structured answer.

The result? The AI explicitly credits *which* perspective contributed *what* insight, providing unprecedented transparency and depth.

*Created by **Ameen Saeed** (Copyright © 2026).*

---

## 🚀 Why Thought Fork?

Standard LLM queries suffer from "averaging"—they give you the safest, most generic middle-ground answer. 
Thought Fork solves this by forcing the model to argue with itself from distinct angles before concluding.

**Features:**
- 🧠 **Dynamic Stance Selection:** The engine analyzes your prompt and automatically invents the perfect reasoning personas (e.g., *a pragmatic-startup-builder*, *a long-term-code-quality-advocate*, and *a performance-focused-engineer*).
- ⚡ **Parallel Execution:** Forks are resolved concurrently using `asyncio`.
- 🧬 **Attributed Convergence (Synthesis):** The final output weaves the parallel thoughts together, explicitly crediting the source of each idea and resolving contradictions.
- 📡 **Server-Sent Events (SSE) Streaming:** Fully built-in SSE support for real-time frontend streaming of parallel forks.

---

## 📦 Installation

```bash
pip install thought-fork
```

### Requirements
- Python 3.10+
- `openai` (used as the universal async client)
- `pydantic`

---

## 🔑 Configuration (Bring Your Own API)

Thought Fork is provider-agnostic. Because it relies on the universal `AsyncOpenAI` client, you can use **OpenAI**, **Anthropic** (via OpenRouter), **Gemini**, or **Local Models** (like Ollama).

By default, the library expects your API key in the environment variables:
```bash
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"
```

You can also pass the configuration explicitly in code using `ForkConfig`:

```python
from thought_fork import ForkConfig
from openai import AsyncOpenAI

# 1. OpenAI Directly
config = ForkConfig(
    api_key="sk-proj-...",
    api_base_url="https://api.openai.com/v1",
    fork_model="gpt-4o-mini",
    synthesis_model="gpt-4o",
    stance_selector_model="gpt-4o-mini"
)

# 2. Google Gemini (via OpenAI compatibility)
config = ForkConfig(
    api_key="your-google-api-key",
    api_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    fork_model="gemini-2.0-flash",
    synthesis_model="gemini-2.0-pro-exp",
    stance_selector_model="gemini-2.0-flash"
)

# 3. Local Models (Ollama / vLLM)
# API key is automatically bypassed for localhost URLs
config = ForkConfig(
    api_base_url="http://localhost:11434/v1",
    fork_model="llama3",
    synthesis_model="llama3",
    stance_selector_model="llama3"
)

# 4. Anthropic / Any Provider via OpenRouter (Default)
config = ForkConfig(
    api_key="sk-or-v1-...",
    api_base_url="https://openrouter.ai/api/v1",
    fork_model="anthropic/claude-haiku-4.5",
    synthesis_model="anthropic/claude-sonnet-4-6",
    stance_selector_model="anthropic/claude-haiku-4.5"
)

# 5. Enterprise BYOC (Bring Your Own Client)
# If you have custom proxies, headers, or httpx settings:
my_client = AsyncOpenAI(api_key="...", default_headers={"X-Custom": "123"})
config = ForkConfig(client=my_client)
```

### Production Resilience
Thought Fork v0.6+ is designed for production reliability:
- **Concurrency Limiting:** `max_concurrent_forks=5` protects against 429 rate limits.
- **Automatic Retries:** `max_retries=2` silently handles 502 Bad Gateway errors with exponential backoff.
- **Graceful Degradation:** If a fork completely fails, synthesis continues with the remaining successful forks.

---

## 💻 Quickstart (Python SDK)

The easiest way to use Thought Fork is via the `synthesize()` helper function. 

```python
import asyncio
from thought_fork import synthesize, ForkConfig

async def main():
    config = ForkConfig(api_key="your-api-key")
    prompt = "Should I build a monolith or microservices for my new startup?"
    
    # This automatically invents 3 custom stances, runs them in parallel, 
    # and synthesizes the final answer.
    result = await synthesize(prompt, fork_count=3, config=config)
    
    print("--- Synthesis ---")
    print(result.synthesis)
    
    print("\n--- Individual Forks ---")
    for detail in result.fork_details:
        print(f"Fork {detail['id']} ({detail['stance']}): {detail['token_count']} tokens")
    
    print(f"\nTotal tokens: {result.token_usage['total']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Usage (Manual Forks)

If you want to manually specify the stances instead of letting the AI invent them dynamically:

```python
from thought_fork import synthesize

stances = ["cautious", "creative", "pragmatic"]
result = await synthesize(prompt, stances=stances)
```

Or you can use the `ForkManager` directly to build your own custom pipeline (see the `examples/` directory in the repository).

---

## 🌐 The API Engine (FastAPI + SSE)

Thought Fork isn't just a Python library; it ships with a production-ready **FastAPI streaming engine**.

To start the API server locally:
```bash
uvicorn api.main:app --port 8000
```

The server exposes a POST `/fork` endpoint that streams Server-Sent Events (SSE). 

**Event Flow:**
1. `stances_selected` — Emitted first with the AI's chosen personas for the prompt.
2. `fork_start` — Emitted when a specific reasoning path begins.
3. `fork_chunk` — Real-time tokens streamed from parallel forks (interleaved).
4. `fork_done` — Emitted when a fork finishes.
5. `synthesis_chunk` — Real-time tokens for the final convergence.
6. `synthesis_done` — Final event with token usage, timing metrics, and a `session_id`.

*(See `api/streaming.py` for the full implementation.)*

---

## 📜 License & Copyright

Thought Fork is open-source software licensed under the **Apache License 2.0**.

**Copyright © 2026 Ameen Saeed.**
If you use, modify, or distribute this framework, you must include the original copyright notice.

> "A tool is only as good as the perspectives it considers."
