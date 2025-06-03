import json, unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ── Extended orthographic remap ─────────────────────────────────────────
ARABIC_REMAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا",   # hamza/alif variants
    "ٱ": "ا",                       # ALIF WASLA  → bare alif to cover «ٱل»
    "ى": "ي", "ئ": "ي",
    "ؤ": "و",
    "ـ": ""                        # tatweel (kashida)
})

def strip_diacritics(txt: str) -> str:
    """remove harakaat, shadda, sukûn, superscript alif, etc."""
    return ''.join(
        ch for ch in unicodedata.normalize("NFD", txt)
        if not unicodedata.combining(ch)
    )

def normalize(txt: str) -> str:
    """full Arabic normalisation: diacritic-free + letter unification"""
    return strip_diacritics(txt).translate(ARABIC_REMAP).strip()

# ── helper to normalise concatenated token-groups ──────────────────────
def group_key(tok: Dict) -> tuple:
    return tok["surah"], tok["ayah"], tok["word_index"]

def concat_and_normalise(tokens: List[Dict]) -> str:
    glued = ''.join(t["token"] for t in sorted(tokens, key=lambda x: x["token_index"]))
    return normalize(glued)

# ── smart_exact_match  (handles diacritics + ال التعريف) ───────────────
def smart_exact_match(
    query_word: str,
    morphology_path: str | Path
) -> Tuple[Optional[List[Dict]], str]:

    if not Path(morphology_path).exists():
        return None, f"❗ File not found: {morphology_path}"

    # 1️⃣  pre-normalise the query  (الرحمن → الرحمن,  ٱلرَّحْمَٰنِ → الرحمن)
    q_norm = normalize(query_word)

    # 2️⃣  stream & group tokens by word_index
    token_groups: dict[tuple, list] = {}
    with open(morphology_path, encoding="utf-8") as fh:
        for line in fh:
            tok = json.loads(line)
            token_groups.setdefault(group_key(tok), []).append(tok)

    # 3️⃣  compare fully-normalised composites to query
    for key, toks in token_groups.items():
        if concat_and_normalise(toks) == q_norm:
            s, a, w = key
            return toks, f"✅ Match: S{s}:A{a}, word_index={w}"

    # 4️⃣  graceful degradation
    return None, (
        f"The word «{query_word}» is not present in the Qurʾānic morphology "
        "database after normalisation (diacritics & definite-article handling)."
    )

# ── quick demo ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    tokens, note = smart_exact_match("اكتب", "/Users/tameem/Documents/ai-quran-research-assistant/chatbot/clean_data/quran_morphology.jsonl")
    print(note)
    if tokens:
        for t in tokens:
            print(f"{t['token']:<8}  root={t['root']}")