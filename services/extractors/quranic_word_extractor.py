# services/extractors/quranic_word_extractor.py
"""
Stage 2 ‘extract_word()’ – finds the Qurʾānic word/root the user
is asking about using layered heuristics:
Regex rules ➔ GPT-4o mini ➔ fallback to user prompt.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Optional

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------- 1. fast regex patterns --------------------
_PATTERNS: list[re.Pattern] = [
    # ما معنى / ما تفسير ... كلمة X
    re.compile(
        r'(?:(?:ما\s+)?(?:معنى|تفسير|مدلول|مغزى|المغزى|مقصود|دلالة|تفيد)\s+'
        r'(?:من\s+|ب)?(?:تعبير|كلمة|لفظة|لفظ|مفردة|عبارة)\s+)'
        r'([^\s\?\.،؟]+)',
        re.I,
    ),
    # ماذا يعني لفظ X
    re.compile(
        r'(?:(?:ماذا\s+)?يعني(?:\s+اصطلاحًا)?\s+'
        r'(?:لفظة?|كلمة|لفظ|مفردة|عبارة)\s+)'
        r'([^\s\?\.،؟]+)',
        re.I,
    ),
    # فسر / اشرح ... كلمة X
    re.compile(
        r'(?:(?:فسر(?:وا)?|فسِّر|فسّر|اشرح|بيّن|وضح|وضّح|دلّني|دلني|'
        r'أريد|أحتاج|رجاءً?|من\s+فضلك|هل\s+يمكنك)\s+'
        r'(?:على\s+|إلى\s+)?(?:لي\s+)?'
        r'(?:بيان\s+|شرحًا?\s+)?'
        r'(?:معنى\s+)?'
        r'(?:جذر\s+|اشتقاق\s+|أصل\s+)?'
        r'(?:ال)?(?:كلمة|لفظة|لفظ|مفردة|عبارة|تعبير|فعل)\s+)'
        r'([^\s\?\.،؟]+)',
        re.I,
    ),
    # bare "جذر كلمة X"
    re.compile(
        r'(?:جذر|اشتقاق|أصل)\s+'
        r'(?:ال)?(?:كلمة|لفظة|لفظ|فعل)?\s*'
        r'([^\s\?\.،؟]+)',
        re.I,
    ),
]

# ------------- 2. GPT-fallback ---------------------------
_MODEL = "gpt-4o-mini-2024-07-18"
_TIMEOUT_S = 12
_CONF_THRESHOLD = 0.45

_SYS_PROMPT = (
    "You are a precise extractor. "
    "Given an Arabic user question, return ONLY the Qur'anic word "
    "requested. Respond JSON: {\"word\":\"...\",\"confidence\":0.88}."
)


def _regex_layer(text: str) -> Optional[str]:
    for p in _PATTERNS:
        m = p.search(text)
        if m:
            return m.group(1)
    return None


def _llm_layer(txt: str) -> tuple[Optional[str], float]:
    try:
        rsp = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYS_PROMPT},
                {"role": "user", "content": txt},
            ],
            max_tokens=20,
            temperature=0.0,
            timeout=_TIMEOUT_S,
        )
        data = json.loads(rsp.choices[0].message.content)
        return data.get("word"), float(data.get("confidence", 0))
    except Exception as err:  # pragma: no cover
        print(f"[LLM-extract] {type(err).__name__}: {err}", file=sys.stderr)
        return None, 0.0


# ----------- 3. public API --------------------------------
def extract_word(question: str) -> Optional[str]:
    """
    Return the word or `None` if extraction fails
    (→ pipeline will ask the user explicitly).
    """
    # layer 1
    w = _regex_layer(question)
    if w:
        return w

    # layer 2
    llm_word, conf = _llm_layer(question)
    if llm_word and conf >= _CONF_THRESHOLD:
        return llm_word

    # layer 3
    return None