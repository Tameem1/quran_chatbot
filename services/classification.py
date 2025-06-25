# services/classification.py
"""
Stage-1 – LLM-only question classifier
-------------------------------------

 • A single ChatCompletion call decides among 14 canonical classes.
 • A single ChatCompletion call decides among 15 canonical classes.
 • A rich system prompt lists the class names *plus* one Arabic example
   for each class so the model can anchor its reasoning.
 • The assistant must reply with **only** the slug (no extra words).

The downstream pipeline already knows these slugs, so no other code
needs to change.
"""

from __future__ import annotations

import os
import re

from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
# ------------------------------------------------------------------ #
# 1. Canonical label slugs  (keep these stable!)
# ------------------------------------------------------------------ #
LABELS_SLUGS = [
    "meaning_word",                    # 0
    "semantic_context_word",           # 1
    "multiple_contexts_word",          # 2
    "difference_two_words",            # 3
    "root_conjugations_usage",         # 4
    "frequency_word_root",             # 5
    "thematic_classification_roots",   # 6
    "semantic_domain_root",            # 7
    "root_extraction",                 # 8
    "root_ayah_extraction",            # 9
    "roots_by_topic",                  # 10
    "forms_of_root",                   # 11
]

# ------------------------------------------------------------------ #
# 2. LLM configuration
# ------------------------------------------------------------------ #
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL = os.getenv("QURAN_CLASSIFIER_MODEL", "gpt-4o-mini-2024-07-18")
_MAX_TOK = int(os.getenv("QURAN_CLASSIFIER_MAX_TOKENS", "8"))

# ------------------------------------------------------------------ #
# 3. Few-shot system prompt
# ------------------------------------------------------------------ #
_SYS_PROMPT = """
أنت مصنِّف أسئلة قرآنية دقيق جدًا. لديك ١٢ فئة فقط ويجب أن ترجع
*فقط* اسم الشريحة (slug) المطابق.

الفئات مع مثال واحد لكل فئة:

0) meaning_word
   مثال: ما معنى كلمة تبّ في قوله تعالى: «تبت يدا أبي لهب»؟
    اشرح جذر كلمة غفر في القرآن.

1) semantic_context_word
   مثال: ماذا يعني الميزان في سورة الرحمن؟
    كيف يُفهم معنى نور في الآية: "نورٌ على نور"؟
    
2) multiple_contexts_word
   مثال: ما الفرق في معنى كلمة نور بين سورة النور وسورة الحديد؟
    كيف يتغيّر معنى كلمة أمة حسب السياق؟

3) difference_two_words
   مثال: ما الفرق بين القتل والذبح في القرآن؟
    هل هناك فرق بين الرحمة والرأفة؟

4) root_conjugations_usage
   مثال: كيف تُستعمل صيغ جذر كتب المختلفة فى القرآن؟
    في أي مواضع جاء جذر علم بصيغة اسم فاعل؟

5) frequency_word_root
   مثال: كم مرة ورد جذر سجد في القرآن؟
    كم مرة وردت كلمة صبر في سورة البقرة؟

6) thematic_classification_roots
    مثال: أعطني قائمة بالجذور المتعلقة بالحرب في القرآن.
    صنّف لي الكلمات التي تدل على الرحمة والعقاب.

7) semantic_domain_root
    مثال: هل جذر قتل مرتبط فقط بالعنف أم له سياقات أخرى؟
    ما الجذور التي تنتمي لمجال العبادة؟

8) root_extraction
    مثال: ما الجذر الذي اشتُقّت منه كلمة يبتغون؟
    ما الجذر الذي جاءت منه كلمة بدرهم؟
    ما جذر كلمة الإسراء؟

9) root_ayah_extraction
    مثال: أعطني الآيات التي وردت فيها تصريفات جذر دمدم؟
    أعطني الآيات التي وردت فيها كلمة مدهامّتان أو من الجذر دهم؟

10) roots_by_topic
    مثال: ما الجذور التي تدل على الهلاك الجماعي؟
    صنّف الكلمات التي تدل على الغفلة والمعصية.

11) forms_of_root
    مثال: ما تصريفات جذر كتب الواردة في القرآن؟
    ما تصريفات جذر خلق؟
    ما تصريفات جذر عذب؟

✨ بعد التفكير، أعد فقط الـslug المطابق (دون أى نص إضافى).
""".strip()

# ------------------------------------------------------------------ #
# 4. Core helper
# ------------------------------------------------------------------ #
def _llm_label(question: str) -> str:
    """
    Query the LLM and convert its reply to a validated slug.
    Falls back to 'meaning_word' (slug 0) on any parse error.
    """
    rsp = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYS_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=_MAX_TOK,
        temperature=0.0,
    )
    raw = rsp.choices[0].message.content.strip()

    # Accept either slug or index; normalise to slug.
    if raw in LABELS_SLUGS:
        return raw

    # Try to parse an integer index that may have slipped through
    m = re.match(r"\D*?(\d{1,2})", raw)
    if m:
        idx = int(m.group(1))
        if 0 <= idx < len(LABELS_SLUGS):
            return LABELS_SLUGS[idx]

    # Graceful fallback
    return "meaning_word"

# ------------------------------------------------------------------ #
# 5. Public API
# ------------------------------------------------------------------ #
def classify(question: str) -> str:
    """
    Stage-1 entry point: returns one of the 14 canonical slugs.
    """
    return _llm_label(question)


# ------------------------------------------------------------------ #
# 6. Quick self-test
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    tests = [
        "ما معنى كلمة تبّ في قوله تعالى: تبت يدا أبي لهب؟",
        "كم مرة ورد جذر سجد فى القرآن؟",
        "ما الفرق بين القتل والذبح فى القرآن؟",
        "صنّف لى الجذور المتعلقة بالحرب.",
        "ما وزن كلمة استغفر؟ ولماذا جاءت بهذا الوزن؟",
    ]
    for q in tests:
        print(f"Q: {q}\n → {classify(q)}\n")