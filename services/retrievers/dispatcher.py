# services/retrievers/dispatcher.py
"""
Stage-3  ·  Retrieval dispatcher
================================

• Implements the 12-way branching scheme described in the JSON spec.
• Relies on existing low-level helpers:
    – smart_exact_match()          (lemma / word lookup)
    – root_lookup_combined()       (root-analysis row)
• Provides a couple of very small extra helpers (root_match, count, …).
• Always returns a dict that becomes <context/> inside
  pipeline.prompt_builder.build_prompt().
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from utils.arabic import normalize
from utils.paths import MORPHOLOGY_FILE, ROOT_ANALYSIS_FILE, DICTIONARY_FILE

from .morphology_retriever import smart_exact_match
from .root_retriever import root_lookup_combined
from .dictionary_retriever import lookup_definition


# --------------------------------------------------------------------------- #
# 1. Light-weight helpers                                                     #
# --------------------------------------------------------------------------- #
def lemma_match(word: str) -> Tuple[Optional[List[Dict]], str]:
    return smart_exact_match(word)


def lemma_match_surah_filter(word: str, surah: str | None = None):
    # Current version ignores surah filter (needs NLP parsing of question).
    return smart_exact_match(word)


def _all_morph_tokens() -> List[Dict]:
    """Read quran_morphology.jsonl once (very small ≈ 100 KB gzipped)."""
    if not hasattr(_all_morph_tokens, "_cache"):
        with open(MORPHOLOGY_FILE, encoding="utf-8") as fh:
            _all_morph_tokens._cache = [json.loads(x) for x in fh]
    return _all_morph_tokens._cache


def root_match(root_or_word: str) -> Tuple[Optional[List[Dict]], str]:
    """
    • If caller passes a *word*, derive its root via smart_exact_match.
    • Otherwise treat argument as a bare root string.
    Then collect **all** tokens with that root.
    """
    tokens, note = smart_exact_match(root_or_word)
    if tokens:
        root = tokens[0]["root"]
    else:
        # assume the target itself is a root
        root = normalize(root_or_word)

    matches = [t for t in _all_morph_tokens() if t["root"] == root]
    if matches:
        return matches, f"✅ Found {len(matches)} tokens with root «{root}»"
    return None, f"Root «{root}» not found in morphology DB."


def pattern_lookup(word: str) -> Tuple[str, str]:
    return "→ (stub) pattern info", "ℹ️  pattern_lookup placeholder"


def etymology_lookup(root: str) -> Tuple[str, str]:
    return "→ (stub) brief etymology", "ℹ️  etymology_lookup placeholder"


def topic_expansion(topic: str) -> Tuple[str, str]:
    return "→ (stub) list of related roots", "ℹ️  topic_expansion placeholder"


def domain_classification(root: str) -> Tuple[str, str]:
    return "→ (stub) semantic domain explanation", "ℹ️  domain_classification placeholder"


# --------------------------------------------------------------------------- #
# 2. Dispatch map (slug → ordered retrieval steps)                            #
# --------------------------------------------------------------------------- #
Step = Dict[str, str]        # for readability

DISPATCH_TABLE: Dict[str, List[Step]] = {
    # 0
    "meaning_word": [
        {"method": "lemma_match", "on_fail": "The word you provided does not exist in the Qur'anic database."},
        {"method": "root_lookup_combined"},
    ],
    # 1
    "semantic_context_word": [
        {"method": "lemma_match", "on_fail": "The word or lemma could not be found in the Qur'anic corpus."},
        {"method": "root_lookup_combined"},
    ],
    # 2
    "multiple_contexts_word": [
        {"method": "root_match", "on_fail": "The root could not be located in the Qur'anic corpus."},
        {"method": "root_lookup_combined"},
    ],
    # 3
    "difference_two_words": [
        {"method": "lemma_match", "on_fail": "One or both of the words are not found in the Qur'an."},
        {"method": "root_lookup_combined"},
    ],
    # 4
    "synonyms_antonyms": [
        {"method": "lemma_match", "on_fail": "The word is not present in the Qur'anic corpus."},
        {"method": "root_lookup_combined"},
    ],
    # 5
    "comparison_near_synonyms": [
        {"method": "lemma_match", "on_fail": "One or more of the provided words are not found in the Qur'an."},
        {"method": "root_lookup_combined"},
    ],
    # 6
    "root_conjugations_usage": [
        {"method": "root_match", "on_fail": "The root was not found in the Qur'anic corpus."},
    ],
    # 7
    "morphological_weight_analysis": [
        {"method": "lemma_match", "on_fail": "The word is not found in the Qur'anic morphology database."},
        {"method": "pattern_lookup"},
    ],
    # 8
    "linguistic_origin_root": [
        {"method": "root_lookup_combined", "on_fail": "The root is not documented in our classical root database."},
        {"method": "etymology_lookup"},
    ],
    # 9
    "frequency_word_root": [
        {"method": "lemma_match_surah_filter", "on_fail": "The word was not found in the specified surah."},
        {"postprocess": "count"},
    ],
    # 10
    "thematic_classification_roots": [
        {"method": "semantic_filter"},        # placeholder → uses root_lookup_combined internally
        {"method": "topic_expansion"},
    ],
    # 11
    "semantic_domain_root": [
        {"method": "root_match", "on_fail": "The root could not be found in the Qur'anic text."},
        {"method": "root_lookup_combined"},
        {"method": "domain_classification"},
    ],
}


# --------------------------------------------------------------------------- #
# 3. Method name → callable map                                               #
# --------------------------------------------------------------------------- #
CALLABLES = {
    "lemma_match": lemma_match,
    "lemma_match_surah_filter": lemma_match_surah_filter,
    "root_match": root_match,
    "root_lookup_combined": root_lookup_combined,
    "pattern_lookup": pattern_lookup,
    "etymology_lookup": etymology_lookup,
    "semantic_filter": lambda x: ("→ (stub) filtered list", "ℹ️  semantic_filter placeholder"),
    "topic_expansion": topic_expansion,
    "domain_classification": domain_classification,
}


# --------------------------------------------------------------------------- #
# 4. Dispatcher entry-point                                                   #
# --------------------------------------------------------------------------- #
def dispatch_retrieval(question_type: str, target: str) -> Dict:
    """
    Stage-3 entry: run the retrieval steps declared for `question_type`
    and return a context dict **without** lemma_match keys.
    """
    steps = DISPATCH_TABLE.get(question_type)
    if not steps:
        return {"error_message": f"❗ Unknown question_type slug: {question_type}"}

    ctx: Dict = {}
    morph_cache: Optional[List[Dict]] = None   # keeps lemma/root data privately

    for i, step in enumerate(steps, 1):

        # ─── post-process steps (e.g. "count") ─────────────────────────
        if "postprocess" in step:
            if step["postprocess"] == "count" and morph_cache:
                ctx["occurrence_count"] = len(morph_cache)
            continue

        method_name = step["method"]

        # ─── SPECIAL: root_lookup_combined needs the root from morphology ─
        # services/retrievers/dispatcher.py
# … previous code unchanged …

        if method_name == "root_lookup_combined":
            # ── NEW: find the *first* token that actually carries a root ──
            root_arg = None
            if morph_cache:
                for tok in morph_cache:            # ① iterate tokens
                    root_field = tok.get("root")
                    if root_field:                 # ② non-empty root found
                        root_arg = root_field
                        break
            if root_arg is None:                   # ③ ultimate fallback
                root_arg = target

            data, note = root_lookup_combined(root_arg)
            ctx[f"{method_name}_note"] = note
            if data:
                ctx[method_name] = data
            else:
                fail_msg = step.get("on_fail")
                if fail_msg:
                    ctx["error_message"] = fail_msg
                    return ctx
            continue

        # ─── METHODS TO BE **OMITTED** FROM ctx  (lemma_match …) ───────
        if method_name in {"lemma_match", "lemma_match_surah_filter"}:
            morph_cache, _note = CALLABLES[method_name](target)
            # on-fail handling
            if morph_cache is None:
                fail_msg = step.get("on_fail")
                if fail_msg:
                    ctx["error_message"] = fail_msg
                    return ctx
            # DO NOT add to ctx → keeps <context> clean
            continue

        # ─── normal retrieval steps (pattern_lookup, root_match, …) ────
        func = CALLABLES.get(method_name)
        if func is None:
            ctx[f"step_{i}_note"] = f"⚠️  Method «{method_name}» not implemented."
            continue

        data, note = func(target)
        ctx[f"{method_name}_note"] = note
        if data:
            ctx[method_name] = data
        else:
            fail_msg = step.get("on_fail")
            if fail_msg:
                ctx["error_message"] = fail_msg
                return ctx

    return ctx