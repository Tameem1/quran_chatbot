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

from utils.arabic import normalize, strip_diacritics
from utils.paths import MORPHOLOGY_FILE


# ── helper: load / group tokens into full Qurʾānic "words" ─────────────
def _group_key(tok: Dict) -> tuple:
    return tok["surah"], tok["ayah"], tok["word_index"]


def _concat(tokens: List[Dict]) -> str:
    """Concatenate raw tokens preserving order in the verse‐word."""
    return "".join(t["token"] for t in sorted(tokens, key=lambda x: x["token_index"]))


# ── spelling-variant generator ─────────────────────────────────────────
_PROCLITICS: Set[str] = {"ك", "ف", "ب", "ل", "س", "و"}  # keep و as *optional* only

# Imperfect-verb prefixes that can follow the future particle «س»
_IMPF_PREFIXES: Set[str] = {"أ", "إ", "آ", "ي", "ت", "ن"}

def _variants(word: str, root_initial: str | None = None) -> Set[str]:
    """
    Generate a small set of orthographic variants that differ by:
        • leading proclitic (one char from _PROCLITICS)
        • leading definite article «ال»
        • trailing case-seat «ا»
        • tanween (ً ٍ ٌ)
    The word itself is always included.
    """
    
    forms: Set[str] = {word}
    

    # ── 1. optional removal of a *single* proclitic  ─────────────────
    # We apply tighter heuristics so that we never strip a letter that is
    # actually the first radical of the root (e.g. «س» in «سابق»).
    if len(word) > 3 and word[0] in _PROCLITICS:
        # Skip if the letter seems to belong to the root itself
        if root_initial and word[0] == root_initial:
            pass  # do NOT remove – keeps integrity of root-initial
        else:
            # Special case «س+» : only future-particle when followed by an
            # imperfect prefix.
            if word[0] == "س":
                if word[1] in _IMPF_PREFIXES:
                    forms.add(word[1:])
            else:
                forms.add(word[1:])
        

    tmp = set(forms)  # snapshot before next rules

    # remove definite article
    for w in tmp:
        if w.startswith("ال") and len(w) > 3:
            forms.add(w[2:])
            

    # remove tanween and trailing alif
    for w in list(forms):
        # Remove tanween
        if "ً" in w:
            forms.add(w.replace("ً", ""))
        if "ٍ" in w:
            forms.add(w.replace("ٍ", ""))
        if "ٌ" in w:
            forms.add(w.replace("ٌ", ""))
        # Remove trailing alif
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

    # Normalize the query word by removing diacritics
    q_norm = normalize(query_word)

    # 2️⃣  read once, group tokens
    token_groups: dict[tuple, list] = {}
    with f.open(encoding="utf-8") as fh:
        for line in fh:
            tok = json.loads(line)
            token_groups.setdefault(_group_key(tok), []).append(tok)

    # 3️⃣  iterate groups, compare variants sets
    for key, toks in token_groups.items():
        # First check if the lemma matches (most strict)
        lemma = toks[0].get("lemma", "")
        if lemma:
            lemma_norm = normalize(lemma)
  
            if lemma_norm == q_norm:
                s, a, w = key
                print(f"🔍 [DEBUG] Found exact lemma match: '{query_word}' in S{s}:A{a}, word_index={w}")
                return toks, f"✅ Exact lemma match: S{s}:A{a}, word_index={w}"

        # Then check if the surface form of the **whole Qurʾānic word** matches
        # A Qurʾānic "word" may consist of multiple tokens (e.g.
        # «أَبَانَا» → ["أَبَا", "نَا"]).  We therefore concatenate the tokens
        # first and compare against the query word – after normalisation – using
        # the spelling-variant helper.

        surface = _concat(toks)
        surface_norm = normalize(surface)

        # Generate small variant sets for robust matching
        query_forms   = _variants(q_norm)
        root_initial  = (toks[0].get("root") or "")[:1] if toks[0].get("root") else None
        surface_forms = _variants(surface_norm, root_initial)

        if query_forms & surface_forms:
            s, a, w = key
            print(f"🔍 [DEBUG] Found surface match: '{query_word}' in S{s}:A{a}, word_index={w}")
            return toks, f"✅ Surface match: S{s}:A{a}, word_index={w}"

        # Finally, if surface matching failed, fall back to root comparison
        root = toks[0].get("root", "")
        if root:
            root_norm = normalize(root)
            if root_norm == q_norm:
                s, a, w = key
                print(f"🔍 [DEBUG] Found exact root match: '{query_word}' in S{s}:A{a}, word_index={w}")
                return toks, f"✅ Exact root match: S{s}:A{a}, word_index={w}"

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