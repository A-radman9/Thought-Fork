# 🔀 Thought Fork

**فرّع تفكير الذكاء الاصطناعي حقك زي ما تفرّع فروع Git.**

Thought Fork هو فريم وورك (إطار عمل) بالبايثون يقدم فكرة **التجميع المنسوب** (Attributed Convergence) للذكاء الاصطناعي. بدال ما تطلب من الذكاء الاصطناعي يعطيك إجابة وحدة عامة، النظام هذا يبتكر بشكل ديناميكي $N$ وجهات نظر مختلفة (زوايا تفكير) مفصلة على مقاس سؤالك بالضبط، ويقسم الذكاء الاصطناعي لمسارات تفكير متوازية (تشتغل مع بعض)، وبعدين يدمجها كلها في إجابة نهائية وحدة ومرتبة.

النتيجة؟ الذكاء الاصطناعي يوضح لك صراحةً *أي* زاوية تفكير جابت *أي* فكرة، وهالشي يعطيك شفافية وعمق مستحيل تشوفه بالوضع العادي.

*من تصميم **أمين سعيد** (حقوق النشر © 2026).*

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

إطار Thought Fork ما يهمه وش مزود الخدمة اللي تستخدمه. لأنه يعتمد على `AsyncOpenAI`، تقدر تستخدم **OpenAI**، أو **Anthropic** (عن طريق OpenRouter)، أو **Gemini**، أو حتى **النماذج المحلية** (زي Ollama).

افتراضياً، المكتبة تتوقع إن مفتاح الـ API حقك موجود في متغيرات البيئة (Environment variables):
```bash
export OPENROUTER_API_KEY="your-key-here"
# أو
export OPENAI_API_KEY="your-key-here"
```

وتقدر طبعاً تمرر الإعدادات مباشرة في الكود باستخدام `ForkConfig`:

```python
from thought_fork import ForkConfig
from openai import AsyncOpenAI

# 1. استخدام OpenAI مباشرة
config = ForkConfig(
    api_key="sk-proj-...",
    api_base_url="https://api.openai.com/v1",
    fork_model="gpt-4o-mini",
    synthesis_model="gpt-4o",
    stance_selector_model="gpt-4o-mini"
)

# 2. استخدام Google Gemini
config = ForkConfig(
    api_key="your-google-api-key",
    api_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    fork_model="gemini-2.0-flash",
    synthesis_model="gemini-2.0-pro-exp",
    stance_selector_model="gemini-2.0-flash"
)

# 3. النماذج المحلية (Ollama / vLLM)
# ما يحتاج API key للروابط المحلية (localhost)
config = ForkConfig(
    api_base_url="http://localhost:11434/v1",
    fork_model="llama3",
    synthesis_model="llama3",
    stance_selector_model="llama3"
)

# 4. Anthropic أو أي موديل عبر OpenRouter (وهذا الافتراضي)
config = ForkConfig(
    api_key="sk-or-v1-...",
    api_base_url="https://openrouter.ai/api/v1",
    fork_model="anthropic/claude-haiku-4.5",
    synthesis_model="anthropic/claude-sonnet-4-6",
    stance_selector_model="anthropic/claude-haiku-4.5"
)

# 5. للشركات المتقدمة (استخدم عميلك الخاص)
# لو عندك بروكسي أو هيدرز مخصصة:
my_client = AsyncOpenAI(api_key="...", default_headers={"X-Custom": "123"})
config = ForkConfig(client=my_client)
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

## 📜 الرخصة وحقوق النشر

برنامج Thought Fork مفتوح المصدر ومرخص تحت **رخصة أباتشي 2.0 (Apache License 2.0)**.

**حقوق النشر © 2026 أمين سعيد.**
لو استخدمت أو عدلت أو وزعت هذا الإطار، لازم ترفق إشعار حقوق النشر الأصلي.

> "قوة الأداة ما تتجاوز قوة الزوايا اللي تفكر منها."
