# services/retrievers/morphology_retriever.py
"""
smart_exact_match()   – resilient, zero-dependency matcher

  • Uses utils.arabic.normalize()  ⟶  unifies hamza/alif & removes diacritics
  • Generates spelling *variants* for both query and token strings.
  • A match succeeds if *any* variant of the query equals *any*
    variant of the token.

This solves:
    – العهن  ↔  كالعهن
    – كالعهن  ↔  العهن
    – وفدا    ↔  وفد
    – dagger-alif and other harakāt
without mutilating the underlying data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from utils.arabic import normalize
from utils.paths import MORPHOLOGY_FILE


# ── helper: load / group tokens into full Qurʾānic “words” ─────────────
def _group_key(tok: Dict) -> tuple:
    return tok["surah"], tok["ayah"], tok["word_index"]


def _concat(tokens: List[Dict]) -> str:
    """Concatenate raw tokens preserving order in the verse‐word."""
    return "".join(t["token"] for t in sorted(tokens, key=lambda x: x["token_index"]))


# ── spelling-variant generator ─────────────────────────────────────────
_PROCLITICS: Set[str] = {"ك", "ف", "ب", "ل", "س", "و"}  # keep و as *optional* only

def _variants(word: str) -> Set[str]:
    """
    Generate a small set of orthographic variants that differ by:
        • leading proclitic (one char from _PROCLITICS)
        • leading definite article «ال»
        • trailing case-seat «ا»
    The word itself is always included.
    """
    forms = {word}

    # remove ONE leading proclitic
    if len(word) > 3 and word[0] in _PROCLITICS:
        forms.add(word[1:])

    tmp = set(forms)  # snapshot before next rules

    # remove definite article
    for w in tmp:
        if w.startswith("ال") and len(w) > 3:
            forms.add(w[2:])

    # remove trailing ‘ا’ seat (e.g. وفدا → وفد)
    for w in list(forms):
        if w.endswith("ا") and len(w) > 3:
            forms.add(w[:-1])

    return forms


# ── main public function ──────────────────────────────────────────────
def smart_exact_match(
    query_word: str,
    morphology_path: str | Path = MORPHOLOGY_FILE,
) -> Tuple[Optional[List[Dict]], str]:
    """
    Lookup tolerant to:
      • diacritics / dagger-alif
      • definite article
      • proclitics: ك ف ب ل س و
      • final tanwīn seat «ا»
    Returns (token_list, note) or (None, error note)
    """
    f = Path(morphology_path)
    if not f.exists():
        return None, f"❗ morphology file not found: {f}"

    # 1️⃣  pre-normalise & build variants of the query
    q_norm = normalize(query_word)
    q_variants = _variants(q_norm)

    # 2️⃣  read once, group tokens
    token_groups: dict[tuple, list] = {}
    with f.open(encoding="utf-8") as fh:
        for line in fh:
            tok = json.loads(line)
            token_groups.setdefault(_group_key(tok), []).append(tok)

    # 3️⃣  iterate groups, compare variant sets
    for key, toks in token_groups.items():
        tok_norm = normalize(_concat(toks))
        if q_variants & _variants(tok_norm):           # non-empty intersection
            s, a, w = key
            return toks, f"✅ Match: S{s}:A{a}, word_index={w}"

    # 4️⃣  not found
    return None, (
        f"The word «{query_word}» was not located in the morphology database "
        "after normalisation and variant matching."
    )


# ── quick self-test ──────────────
if __name__ == "__main__":
    tests = ["العهن", "كالعهن", "عهن", "وفد", "وفدا"]
    for w in tests:
        res, note = smart_exact_match(w)
        print(f"{w:<6} → {'✅' if res else '❌'}  {note}")