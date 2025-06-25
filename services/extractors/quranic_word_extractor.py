# services/extractors/quranic_word_extractor.py
"""
Stage 2 'extract_word()' – finds the Qurʾānic word/root the user
is asking about using layered heuristics:
Regex rules ➔ GPT-4o mini ➔ fallback to user prompt.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Optional, Tuple

from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
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
        r'(?:(?:فسر(?:وا)?|فسِّر|فسّر|اشرح|بيّن|وضح|وضّح|دلّني|دلني|'
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
        r'(?:ال)?(?:كلمة|لفظة|لفظ|فعل)\s+'
        r'([^\s\?\.،؟]+)',
        re.I,
    ),
    # "تصريفات جذر X" or directly "جذر X" (without the word 'كلمة')
    re.compile(
        r'(?:تصريفات|تصاريف)?\s*(?:جذر)\s+([^\s\?\.،؟]+)',
        re.I,
    ),
    # Special pattern for words with hamza
    re.compile(
        r'(?:كلمة|لفظة|لفظ|مفردة|عبارة)\s+'
        r'([أإآ][^\s\?\.،؟]+)',
        re.I,
    ),
    # Generic "… كلمة X" pattern (placed last to catch remaining cases)
    re.compile(
        r'(?:كلمة|لفظة|لفظ|مفردة|عبارة)\s+([^\s\?\.،؟]+)',
        re.I,
    ),
]

# ------------- 1.5. Two-word patterns for difference questions --------------------
_TWO_WORD_PATTERNS: list[re.Pattern] = [
    # ما الفرق بين X و Y (where Y might start with و)
    re.compile(
        r'(?:ما\s+الفرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # هل هناك فرق بين X و Y (where Y might start with و)
    re.compile(
        r'(?:هل\s+هناك\s+فرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # الفرق بين X و Y (where Y might start with و)
    re.compile(
        r'(?:الفرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # ما الفرق في معنى X و Y (where Y might start with و)
    re.compile(
        r'(?:ما\s+الفرق\s+في\s+معنى\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # Generic pattern for "difference between X and Y"
    re.compile(
        r'(?:.*?فرق.*?بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # Alternative pattern for cases where و is attached to the second word
    re.compile(
        r'(?:.*?فرق.*?بين\s+)'
        r'([^\s\?\.،؟]+)\s+و([^\s\?\.،؟]+)',
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
    "requested. For words starting with hamza (أ, إ, آ), preserve the hamza exactly as written. "
    "Respond JSON: {\"word\":\"...\",\"confidence\":0.88}."
)

_SYS_PROMPT_TWO_WORDS = (
    "You are a precise extractor for difference questions. "
    "Given an Arabic question asking about the difference between two words, "
    "return ONLY the two words separated by '|'. "
    "For words starting with hamza (أ, إ, آ), preserve the hamza exactly as written. "
    "Respond JSON: {\"words\":\"word1|word2\",\"confidence\":0.88}."
)


def _regex_layer(text: str) -> Optional[str]:
    print(f"\n🔍 Extracting word from: {text}")
    for i, p in enumerate(_PATTERNS):
        m = p.search(text)
        if m:
            word = m.group(1)
            print(f"Pattern {i} matched: {word}")
            # Ignore common relative pronouns accidentally captured (e.g. "ذي", "الذي")
            if word in {"ذي", "الذي", "التي", "الذين", "اللذان", "اللذين", "اللتان", "اللاتي", "اللائي"}:
                continue  # keep searching other patterns
            return word
    print("No pattern matched")
    return None


def _regex_layer_two_words(text: str) -> Optional[Tuple[str, str]]:
    print(f"\n🔍 Extracting two words from: {text}")
    for i, p in enumerate(_TWO_WORD_PATTERNS):
        m = p.search(text)
        if m:
            word1 = m.group(1)
            word2 = m.group(2)

            # Do NOT strip initial letters; patterns already exclude the conjunctive و
            print(f"Two-word pattern {i} matched: {word1} and {word2}")
            return word1, word2
    print("No two-word pattern matched")
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


def _llm_layer_two_words(txt: str) -> tuple[Optional[Tuple[str, str]], float]:
    try:
        rsp = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYS_PROMPT_TWO_WORDS},
                {"role": "user", "content": txt},
            ],
            max_tokens=30,
            temperature=0.0,
            timeout=_TIMEOUT_S,
        )
        data = json.loads(rsp.choices[0].message.content)
        words_str = data.get("words", "")
        if "|" in words_str:
            word1, word2 = words_str.split("|", 1)
            return (word1.strip(), word2.strip()), float(data.get("confidence", 0))
        return None, 0.0
    except Exception as err:  # pragma: no cover
        print(f"[LLM-extract-two-words] {type(err).__name__}: {err}", file=sys.stderr)
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


def extract_two_words(question: str) -> Optional[Tuple[str, str]]:
    """
    Return a tuple of two words or `None` if extraction fails
    (→ pipeline will ask the user explicitly).
    """
    # layer 1: regex patterns
    words = _regex_layer_two_words(question)
    if words:
        return words

    # layer 2: LLM fallback
    llm_words, conf = _llm_layer_two_words(question)
    if llm_words and conf >= _CONF_THRESHOLD:
        return llm_words

    # layer 3: fallback
    return None