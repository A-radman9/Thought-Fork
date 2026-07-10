# 🔀 Thought Fork

**Branch your AI's reasoning like Git branches.**

Thought Fork is a Python framework that introduces **Attributed Convergence** to AI reasoning. Instead of asking a single AI model to give you one generic answer, Thought Fork dynamically invents $N$ distinct reasoning perspectives (stances) tailored to your specific prompt, branches the AI into parallel reasoning streams, and then merges them back together into a single, synthesized, highly-structured answer.

The result? The AI explicitly credits *which* perspective contributed *what* insight, providing unprecedented transparency and depth.



*(Scroll down for Arabic | انزل تحت للشرح بالعربي)*

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

Thought Fork is provider-agnostic. Because it relies on the universal `AsyncOpenAI` client, you can use **OpenAI**, **Anthropic**, **Gemini**, **Groq**, **Nvidia**, or **Local Models** (like Ollama or LM Studio).

The easiest way to configure your provider is by creating a `.env` file in your project root. Just set your provider's base URL, model, and API key:

```env
# Example 1: Local Ollama (No API key needed)
THOUGHT_FORK_API_BASE=http://localhost:11434/v1
THOUGHT_FORK_MODEL=llama3

# Example 2: Groq Cloud
# THOUGHT_FORK_API_BASE=https://api.groq.com/openai/v1
# THOUGHT_FORK_MODEL=llama-3.3-70b-versatile
# THOUGHT_FORK_API_KEY=your-groq-api-key
```

Thought Fork will automatically pick up these settings. If you want to override the `.env` manually in your code, you can use `ForkConfig`:

```python
from thought_fork import ForkConfig

# Manually configuring the provider in code
config = ForkConfig(
    api_base_url="https://api.openai.com/v1",
    fork_model="gpt-4o-mini",
    synthesis_model="gpt-4o",
    api_key="your-api-key-here"
)
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



> "A tool is only as good as the perspectives it considers."

<br>
<hr>
<br>

# 🔀 Thought Fork (بالعربي)

**فرّع تفكير الذكاء الاصطناعي حقك زي ما تفرّع فروع Git.**

Thought Fork هو فريم وورك (إطار عمل) بالبايثون يقدم فكرة **التجميع المنسوب** (Attributed Convergence) للذكاء الاصطناعي. بدال ما تطلب من الذكاء الاصطناعي يعطيك إجابة وحدة عامة، النظام هذا يبتكر بشكل ديناميكي $N$ وجهات نظر مختلفة (زوايا تفكير) مفصلة على مقاس سؤالك بالضبط، ويقسم الذكاء الاصطناعي لمسارات تفكير متوازية (تشتغل مع بعض)، وبعدين يدمجها كلها في إجابة نهائية وحدة ومرتبة.

النتيجة؟ الذكاء الاصطناعي يوضح لك صراحةً *أي* زاوية تفكير جابت *أي* فكرة، وهالشي يعطيك شفافية وعمق مستحيل تشوفه بالوضع العادي.



---

## 🚀 ليه تستخدم Thought Fork؟

الأسئلة العادية للنماذج اللغوية (LLMs) تعاني من مشكلة "أخذ المتوسط"—يعني دايماً يعطونك الإجابة الأكثر أماناً واللي تناسب الكل. 
هنا يجي Thought Fork يحل هالمشكلة بانه يجبر النموذج إنه يتجادل مع نفسه من زوايا مختلفة ومتباينة قبل لا يعطيك الخلاصة.

**المميزات:**
- 🧠 **اختيار ديناميكي لزوايا التفكير:** المحرك يحلل سؤالك ومباشرة يبتكر شخصيات تفكير مناسبة (مثلاً: *مبرمج-حريص-على-الجودة*، *مؤسس-شركة-عملي*، *مهندس-مهووس-بالأداء*).
- ⚡ **تشغيل متوازي:** كل الفروع تشتغل بنفس الوقت باستخدام `asyncio` عشان ما نضيع وقتك.
- 🧬 **تجميع منسوب (Synthesis):** الإجابة النهائية تدمج كل الأفكار المتوازية مع بعض، وتعطي الكريدت (الفضل) لصاحب الفكرة، وتحل أي تناقضات بينهم.
- 📡 **بث حي (SSE Streaming):** دعم كامل للـ Server-Sent Events عشان تقدر تبث الأفكار المتوازية لايف على الواجهة الأمامية (Frontend).

---

## 📦 التثبيت

```bash
pip install thought-fork
```

### المتطلبات
- بايثون 3.10+
- مكتبة `openai` (نستخدمها كعميل أساسي لكل الموديلات)
- مكتبة `pydantic`

---

## 🔑 الإعدادات (جيب الـ API حقك)

إطار Thought Fork ما يهمه وش مزود الخدمة اللي تستخدمه. لأنه يعتمد على `AsyncOpenAI`، تقدر تستخدم **OpenAI**، أو **Anthropic**، أو **Gemini**، أو **Groq**، أو **Nvidia**، أو حتى **النماذج المحلية** (زي Ollama و LM Studio).

أسهل طريقة تضبط فيها إعداداتك هي عن طريق ملف `.env` في مشروعك. بس حط رابط المزود (API Base)، واسم الموديل، والمفتاح السري:

```env
# مثال 1: استخدام Ollama محلياً (بدون مفتاح سري)
THOUGHT_FORK_API_BASE=http://localhost:11434/v1
THOUGHT_FORK_MODEL=llama3

# مثال 2: استخدام Groq السحابي
# THOUGHT_FORK_API_BASE=https://api.groq.com/openai/v1
# THOUGHT_FORK_MODEL=llama-3.3-70b-versatile
# THOUGHT_FORK_API_KEY=your-groq-api-key
```

إطار Thought Fork راح يسحب هذي الإعدادات تلقائياً. ولو حبيت تتجاوز ملف الـ `.env` وتمرر الإعدادات مباشرة داخل الكود، تقدر تستخدم `ForkConfig` بهالشكل:

```python
from thought_fork import ForkConfig

# تمرير الإعدادات مباشرة في الكود
config = ForkConfig(
    api_base_url="https://api.openai.com/v1",
    fork_model="gpt-4o-mini",
    synthesis_model="gpt-4o",
    api_key="your-api-key-here"
)
```

### الاعتمادية للإنتاج (Production Resilience)
نسخة Thought Fork v0.6+ مصممة عشان تكون قوية في بيئة الإنتاج:
- **تحديد التزامن (Concurrency Limiting):** `max_concurrent_forks=5` تحميك من حظر الـ 429 Too Many Requests.
- **إعادة المحاولة التلقائية:** `max_retries=2` تتعامل بصمت مع أخطاء 502 وترجع تحاول (Exponential backoff).
- **التعامل المرن مع الأخطاء:** لو فشل فرع من الفروع تماماً، عملية التجميع (Synthesis) تكمل شغلها وتدمج الفروع الباقية اللي نجحت بدون ما يكرش النظام.

---

## 💻 البداية السريعة (Python SDK)

أسهل طريقة تستخدم فيها Thought Fork هي دالة `synthesize()`.

```python
import asyncio
from thought_fork import synthesize, ForkConfig

async def main():
    config = ForkConfig(api_key="your-api-key")
    prompt = "هل الأفضل أبني مشروعي كـ Monolith أو Microservices؟"
    
    # هالسطر بيبتكر 3 زوايا تفكير، ويشغلهم بنفس الوقت، ويعطيك الخلاصة.
    result = await synthesize(prompt, fork_count=3, config=config)
    
    print("--- الخلاصة (Synthesis) ---")
    print(result.synthesis)
    
    print("\n--- الفروع الفردية (Individual Forks) ---")
    for detail in result.fork_details:
        print(f"الفرع {detail['id']} ({detail['stance']}): استخدم {detail['token_count']} توكنز")
    
    print(f"\nإجمالي التوكنز: {result.token_usage['total']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### استخدام متقدم (حدد الزوايا بنفسك)

لو كنت تبي تحدد زوايا التفكير يدوياً بدال ما تخلي الذكاء الاصطناعي يبتكرها لك:

```python
from thought_fork import synthesize

stances = ["cautious", "creative", "pragmatic"]
result = await synthesize(prompt, stances=stances)
```

أو تقدر تستخدم `ForkManager` مباشرة عشان تبني البايبلاين الخاص فيك (شيك على مجلد `examples/` في الريبو).

---

## 🌐 محرك الـ API (استخدام FastAPI + SSE)

مشروع Thought Fork مو بس مكتبة بايثون؛ هو يجي مع محرك بث **FastAPI** جاهز للإنتاج.

عشان تشغل السيرفر المحلي:
```bash
uvicorn api.main:app --port 8000
```

السيرفر يوفر نقطة نهاية POST `/fork` تبث البيانات حية بنظام (SSE).

**كيف يمشي التسلسل؟**
1. `stances_selected` — تنرسل أول شيء وتعلمك وش الشخصيات اللي اختارها الذكاء الاصطناعي.
2. `fork_start` — تنرسل أول ما يبدأ مسار تفكير معين.
3. `fork_chunk` — نصوص حية (Tokens) تجي من الفروع المتوازية (مدموجة مع بعض).
4. `fork_done` — تنرسل لا خلص الفرع.
5. `synthesis_chunk` — نصوص حية لخلاصة الأفكار.
6. `synthesis_done` — آخر حدث يرسلك إحصائيات التوكنز والوقت والـ `session_id`.

*(تقدر تشوف `api/streaming.py` عشان تفهم التفاصيل الكاملة.)*

---



> "قوة الأداة ما تتجاوز قوة الزوايا اللي تفكر منها."
