from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from utils.arabic import normalize
from utils.paths import MORPHOLOGY_FILE
from services.retrievers.morphology_retriever import _variants, _concat
from services.extractors.quranic_word_extractor import extract_word


class RootAyahExtraction:
    """Stage-2 helper – return **all** ayāt that contain a given Qurʾānic
    *word* **or** *root* (no duplicates).

    Steps:
        1. Detect the target word/root using the same multi-layer logic as
           `extract_word()`.
        2. Load the morphology JSONL once and group tokens → words → verses.
        3. Iterate over every Qurʾānic word applying the *exact* matching logic
           from `smart_exact_match()` (lemma → surface variants → root).
        4. Collect every verse that matches (continue scanning, no early stop).
        5. Reconstruct the full surface text for each matched verse and return
           them ordered by canonical mushaf order (Sūrah then āyah).
    """

    # ------------------------------------------------------------------
    # Shared in-memory caches (populated once per process)
    # ------------------------------------------------------------------
    _VERSE_CACHE: Dict[Tuple[int, int], Dict[int, List[Dict]]] = {}
    _FILE_LOADED: bool = False

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, morphology_path: str | Path | None = None) -> None:
        """Optionally allow overriding the morphology file path (testing)."""
        self._morph_path = Path(morphology_path or MORPHOLOGY_FILE)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, question: str, surah_filter: int | None = None) -> List[Tuple[int,int,str]]:
        """Return a *deduplicated*, *ordered* list of (surah, ayah, text).

        If *surah_filter* is given, only verses from that sūrah are returned."""
        query_word = extract_word(question)
        if not query_word:
            # If the incoming string looks like a single word/root, use it directly
            if 1 <= len(question.strip().split()) <= 2:
                query_word = question.strip()
            else:
                raise ValueError("❓ لم أستطع تحديد الكلمة أو الجذر المطلوب من السؤال.")

        q_norm = normalize(query_word)

        if not self.__class__._FILE_LOADED:
            self._load_morphology()

        matched: Set[Tuple[int, int]] = set()

        for (s, a), words in self.__class__._VERSE_CACHE.items():
            if surah_filter is not None and s != surah_filter:
                continue
            for toks in words.values():
                if self._word_matches(q_norm, toks):
                    matched.add((s, a))
                    break

        output: List[Tuple[int,int,str]] = []
        for s, a in sorted(matched):
            text = self._build_verse_text(self.__class__._VERSE_CACHE[(s, a)])
            output.append((s, a, text))
        return output

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_morphology(self) -> None:
        if not self._morph_path.exists():
            raise FileNotFoundError(f"Morphology file not found: {self._morph_path}")

        verse_map: Dict[Tuple[int, int], Dict[int, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        with self._morph_path.open(encoding="utf-8") as fh:
            for line in fh:
                tok = json.loads(line)
                key = (int(tok["surah"]), int(tok["ayah"]))
                verse_map[key][int(tok["word_index"])].append(tok)

        # Smart cast to plain dicts for smaller memory & faster lookups
        self.__class__._VERSE_CACHE = {k: dict(v) for k, v in verse_map.items()}
        self.__class__._FILE_LOADED = True

    # --------------------------------------------------------------
    def _word_matches(self, q_norm: str, tokens: List[Dict]) -> bool:
        # Helper to add **shadda-free** versions of every string in the set
        def _with_shadda_free(variants: set[str]) -> set[str]:
            return variants | {v.replace("ّ", "") for v in variants}

        # 1) lemma equality (ignore shadda differences)
        for tok in tokens:
            lemma = tok.get("lemma") or ""
            if lemma:
                lem_norm = normalize(lemma)
                if lem_norm == q_norm or lem_norm.replace("ّ", "") == q_norm.replace("ّ", ""):
                    return True

        # 2) surface variant intersection (shadda-robust)
        surface_norm = normalize(_concat(tokens))

        # Prefer the first token that actually carries a root for initial radical
        root_initial = ""
        for tok in tokens:
            rt = tok.get("root")
            if rt:
                root_initial = rt[:1]
                break

        q_forms = _with_shadda_free(_variants(q_norm))
        s_forms = _with_shadda_free(_variants(surface_norm, root_initial))

        if q_forms & s_forms:
            return True

        # 3) root equality (ignore shadda)
        for tok in tokens:
            root = tok.get("root") or ""
            if root:
                r_norm = normalize(root)
                if r_norm == q_norm or r_norm.replace("ّ", "") == q_norm.replace("ّ", ""):
                    return True

        return False

    # --------------------------------------------------------------
    @staticmethod
    def _build_verse_text(word_dict: Dict[int, List[Dict]]) -> str:
        """Reconstruct a verse from grouped tokens."""
        words: List[str] = []
        for idx in sorted(word_dict):
            words.append(_concat(word_dict[idx]))
        return " ".join(words) 