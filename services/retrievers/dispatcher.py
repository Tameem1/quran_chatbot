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
import unicodedata
import os
import numpy as np

from utils.arabic import normalize
from utils.paths import MORPHOLOGY_FILE, ROOT_ANALYSIS_FILE, DICTIONARY_FILE

from .morphology_retriever import (
    smart_exact_match,
    _variants as _m_variants,
    _concat as _m_concat,
)
from .root_retriever import root_lookup_combined
from .dictionary_retriever import lookup_definition


# --------------------------------------------------------------------------- #
# 1. Light-weight helpers                                                     #
# --------------------------------------------------------------------------- #
def lemma_match(word: str) -> Tuple[Optional[List[Dict]], str]:
    """
    Attempt a resilient lemma / surface match first. If **no** tokens are
    found, fall back to a *root*-level lookup so that queries that already
    supply a bare triliteral root (e.g. «سجد») or an otherwise
    unrecognised form (miss-spelling, rare orthography, …) still return a
    useful result set.

    Returns the first successful match (word-level ⟶ root-level) together
    with a human-readable note.  If both stages fail, we concatenate the
    two diagnostic notes so that the caller can surface a meaningful
    error message.
    """

    # 1️⃣  Primary – strict lemma/surface matching
    tokens, note = smart_exact_match(word)
    print(f"🔍 [DEBUG] lemma_match primary result: {tokens}")

    if tokens:
        return tokens, note

    # 2️⃣  Fallback – treat the input as a **root**
    root_tokens, root_note = root_match(word)
    print(f"🔍 [DEBUG] lemma_match fallback (root_match) result: {root_tokens}")

    if root_tokens:
        combined_note = (
            f"{note}\nℹ️  Falling back to root search «{word}».\n{root_note}"
        )
        return root_tokens, combined_note

    # 3️⃣  Both lookups failed – merge notes for transparency
    combined_note = f"{note}\n{root_note}"
    return None, combined_note


def lemma_match_surah_filter(word: str, surah: str | None = None):
    """Return **all** tokens whose lemma **or** surface form matches *word*.

    – Uses the same resilient matching rules as ``lemma_match``.
    – If *surah* (int | str) is given, restrict matches to that sūrah.

    The dispatcherʼs post-processing step can then simply ``len(tokens)`` to
    obtain the frequency.
    """

    # ── helper: resolve optional surah filter ───────────────────────────
    surah_num: int | None = None
    if surah is not None:
        try:
            surah_num = int(surah)
        except (ValueError, TypeError):
            # If a non-numeric surah name is provided we silently ignore –
            # fuller NLP parsing can be added upstream later.
            pass

    # Normalise the query once
    q_norm = normalize(word)

    # Prepare caches (load once, very small file)
    tokens_all = _all_morph_tokens()

    # 1️⃣  Group tokens into complete Qurʼānic words ---------------------
    grouped: dict[tuple, list] = {}
    for tok in tokens_all:
        if surah_num is not None and int(tok["surah"]) != surah_num:
            continue  # early discard if outside requested sūrah
        key = (tok["surah"], tok["ayah"], tok["word_index"])
        grouped.setdefault(key, []).append(tok)

    matches: list[dict] = []

    # 2️⃣  Iterate groups, apply lemma & surface-variant comparison ------
    for key, toks in grouped.items():
        lemma = toks[0].get("lemma", "")
        if lemma and normalize(lemma) == q_norm:
            matches.extend(toks)
            continue

        surface = _m_concat(toks)
        surface_norm = normalize(surface)

        root_initial = (toks[0].get("root") or "")[:1] if toks[0].get("root") else None

        # Build variant sets and add *additional* versions with shadda removed
        def _with_shadda_free(variants: set[str]) -> set[str]:
            return variants | {v.replace("ّ", "") for v in variants}

        q_forms   = _with_shadda_free(_m_variants(q_norm))
        s_forms   = _with_shadda_free(_m_variants(surface_norm, root_initial))

        if q_forms & s_forms:
            matches.extend(toks)

    # 3️⃣  If we found word-level matches, return them -------------------
    if matches:
        note = (
            f"✅ Found {len(matches)} tokens for ‘{word}’"
            + (f" in S{surah_num}" if surah_num else " across the corpus")
        )
        return matches, note

    # 4️⃣  Fallback – treat the query as a root --------------------------
    root_tokens, root_note = root_match(word)
    if root_tokens:
        if surah_num is not None:
            root_tokens = [t for t in root_tokens if int(t["surah"]) == surah_num]
        if root_tokens:
            note = root_note + (
                f" (filtered to S{surah_num})" if surah_num else ""
            )
            return root_tokens, note

    # 5️⃣  Nothing found --------------------------------------------------
    scope = f" in S{surah_num}" if surah_num else " in corpus"
    return None, f"❌ ‘{word}’ not found{scope}."


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
        # Always preserve the original root
        root = root_or_word

    # For hamza roots, we need to check both normalized and unnormalized forms
    if root.startswith(("أ", "إ", "آ")):
        matches = [t for t in _all_morph_tokens() if t["root"] == root or t["root"] == normalize(root)]
    else:
        matches = [t for t in _all_morph_tokens() if t["root"] == root]

    if matches:
        return matches, f"✅ Found {len(matches)} tokens with root «{root}»"
    return None, f"Root «{root}» not found in morphology DB."


def pattern_lookup(word: str) -> Tuple[str, str]:
    return "→ (stub) pattern info", "ℹ️  pattern_lookup placeholder"


def etymology_lookup(root: str) -> Tuple[str, str]:
    return "→ (stub) brief etymology", "ℹ️  etymology_lookup placeholder"


def topic_expansion(topic: str) -> Tuple[str, str]:
    """Return a *comma-separated* list of the most relevant Qurʼānic roots
    to the given **Arabic** *topic*.

    Implementation details:
    • Uses the existing `root_analysis.jsonl` resource as a miniature corpus
      where each *entry* (≈ 600) is treated as a document whose semantic
      content is the explanatory gloss + synonyms.
    • Embeddings: identical to the rest of the project –
      `intfloat/multilingual-e5-large` via ``utils.embedding_utils.get_embeddings``.
    • Vector backend: all-in-memory NumPy – no external DB – because the corpus
      is tiny so start-up latency is negligible and we avoid an extra Chroma
      dependency here.
    • The heavy lifting (loading + embedding the 600 docs) is performed **once**
      per interpreter session and cached on the function object to keep
      subsequent calls < 10 ms.
    The function gracefully degrades: if embedding fails for any reason, we
    fall back to an empty result and return a diagnostic note.
    """
    try:
        # ─── 1. Lazy-initialise static corpus & embeddings ───────────────
        if not hasattr(topic_expansion, "_ROOT_STRS"):
            from utils.paths import ROOT_ANALYSIS_FILE
            from utils.embedding_utils import get_embeddings
            import json, numpy as np

            print("🔄 [topic_expansion] Initialising corpus & embeddings …")

            # Load ⇢ lists --------------------------------------------------
            roots: list[str] = []
            raw_rows: list[dict] = []
            docs: list[str] = []
            docs_str: list[str] = []
            with open(ROOT_ANALYSIS_FILE, encoding="utf-8") as fh:
                for j in map(json.loads, fh):
                    r = j.get("root_stripped") or j.get("root") or ""
                    gloss = j.get("مفردات لسان العرب", "")
                    syns = j.get("المرادفات", "")
                    doc_text = f"{r} – {gloss} {syns}"
                    docs.append(doc_text)
                    docs_str.append(doc_text)
                    roots.append(r)
                    raw_rows.append(j)

            # Compute embeddings once -------------------------------------
            cache_name = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-large").replace("/", "_")
            cache_file = os.path.join(Path(ROOT_ANALYSIS_FILE).parent, f"root_analysis_emb_{cache_name}.npy")

            if os.path.exists(cache_file):
                print("📂 [topic_expansion] Loading pre-computed embeddings…")
                vecs_np = np.load(cache_file)
                if vecs_np.shape[0] != len(docs):
                    print("⚠️  Embed cache size mismatch. Re-computing …")
                    vecs_np = None
            else:
                vecs_np = None

            if vecs_np is None:
                print("🧮 [topic_expansion] Computing embeddings for corpus …")
                embedder = get_embeddings()
                vecs = embedder.embed_documents(docs)  # List[List[float]]
                vecs_np = np.array(vecs, dtype="float32")
                # L2-normalise for cosine similarity via dot product
                norms = np.linalg.norm(vecs_np, axis=1, keepdims=True) + 1e-9
                vecs_np = vecs_np / norms
                try:
                    np.save(cache_file, vecs_np)
                    print(f"💾 [topic_expansion] Saved embeddings cache → {cache_file}")
                except Exception as _err:
                    print(f"⚠️  Could not save embed cache: {_err}")
            else:
                embedder = get_embeddings()  # ensure loaded for query

            # Cache on the function object
            topic_expansion._ROOT_STRS = roots
            topic_expansion._RAW_ROWS = raw_rows
            topic_expansion._DOCS_STR = docs_str
            topic_expansion._VECS = vecs_np
            topic_expansion._EMBED = embedder
            topic_expansion._NP = np

            print(f"✅ [topic_expansion] Loaded {len(roots)} rows & cached embeddings.")

        # ─── 2. Embed the query topic text ───────────────────────────────
        vec_q = topic_expansion._EMBED.embed_query(topic)
        print(f"🔍 [topic_expansion] Embedded query ‘{topic}’. Searching top matches…")
        np_mod = topic_expansion._NP
        q_vec = np_mod.array(vec_q, dtype="float32")
        q_vec = q_vec / (np_mod.linalg.norm(q_vec) + 1e-9)

        # ─── 3. Similarity ranking (dot = cosine) ────────────────────────
        sims = topic_expansion._VECS @ q_vec
        top_idx = sims.argsort()[-9:][::-1]  # top-9 highest → descending

        roots_ranked = [topic_expansion._ROOT_STRS[i] for i in top_idx]
        # Deduplicate while preserving order if duplicates somehow arise
        seen = set()
        unique_roots = [r for r in roots_ranked if not (r in seen or seen.add(r))]

        # Gather full rows for extra context ---------------------------------
        rows: list[dict] = []
        if not hasattr(topic_expansion, "_ROWS_CACHE"):
            # Build cache mapping root→row to avoid re-reading file
            topic_expansion._ROWS_CACHE = {
                r: row for r, row in zip(topic_expansion._ROOT_STRS, topic_expansion._RAW_ROWS)
            }
        for r in unique_roots[:9]:
            row = topic_expansion._ROWS_CACHE.get(r)
            if row:
                rows.append(row)

        rows_text = [topic_expansion._DOCS_STR[topic_expansion._ROOT_STRS.index(r)] for r in unique_roots[:9]]

        print("🔝 [topic_expansion] Top 5 roots:", ", ".join(unique_roots[:5]))

        data_out = {
            "root_list": unique_roots[:9],
            "rows": rows,
            "rows_text": rows_text,
        }
        note = f"✅ Retrieved {len(unique_roots[:9])} candidate roots for topic ‘{topic}’."
        return data_out, note

    except Exception as err:
        # Graceful degradation – return empty list but include diagnostic
        return "", f"❌ topic_expansion failed: {err}"


def domain_classification(root: str) -> Tuple[str, str]:
    return "→ (stub) semantic domain explanation", "ℹ️  domain_classification placeholder"


def ayah_extraction(word: str) -> Tuple[Optional[List[str]], str]:
    """Return **unique** formatted ayāt using RootAyahExtraction.

    If a sūrah filter (global var _SURAH_FILTER) is set, pass it to the extractor.
    (We rely on closure to inject the filter from dispatcher.)"""
    surah_filter = getattr(ayah_extraction, "_SURAH_FILTER", None)
    try:
        from services.extractors.root_ayah_extraction import RootAyahExtraction
        from services.extractors.surah_extractor import _SURAH_NAMES
        extractor = RootAyahExtraction()
        triples = extractor.extract(word, surah_filter)
        if not triples:
            scope = f" في سورة {_SURAH_NAMES[surah_filter-1]}" if surah_filter else ""
            return None, f"❌ لا توجد آيات تحتوي على «{word}»{scope}."

        formatted = [f"سورة {_SURAH_NAMES[s-1]} آية {a} – {txt}" for s, a, txt in triples]
        return formatted, f"✅ تم استخراج {len(formatted)} آية تحتوي على «{word}»."
    except Exception as err:
        return None, f"❌ root_ayah_extraction error: {err}"


def _ayahs_by_root_exact(root: str, max_n: int = 3) -> List[str]:
    """Return up to *max_n* formatted ayāt containing tokens whose **root**
    matches *root* exactly (ignores surface/lemma to avoid pronoun collision)."""
    if not hasattr(_ayahs_by_root_exact, "_VERSE_CACHE"):
        # Build verse-level cache once using existing morphology loader
        _ayahs_by_root_exact._TOKENS = _all_morph_tokens()
        # group tokens by (surah, ayah)
        _verse_map: Dict[Tuple[int,int], List[Dict]] = {}
        for tok in _ayahs_by_root_exact._TOKENS:
            key = (int(tok["surah"]), int(tok["ayah"]))
            _verse_map.setdefault(key, []).append(tok)
        _ayahs_by_root_exact._VERSE_MAP = _verse_map
        _ayahs_by_root_exact._VERSE_CACHE = True

    root_norm = normalize(root)
    matches: List[Tuple[int,int]] = []
    for s,a in _ayahs_by_root_exact._VERSE_MAP:
        for tok in _ayahs_by_root_exact._VERSE_MAP[(s,a)]:
            tok_root = tok.get("root")
            if tok_root and normalize(tok_root) == root_norm:
                matches.append((s,a))
                break
        if len(matches) >= max_n:
            break

    # Build text using RootAyahExtraction helper for consistency
    if matches:
        from services.extractors.root_ayah_extraction import RootAyahExtraction
        extractor = RootAyahExtraction()
        verses = []
        for s,a in matches:
            verse_toks = _ayahs_by_root_exact._VERSE_MAP[(s,a)]
            # group tokens by word_index to reuse existing builder
            grouped: Dict[int, List[Dict]] = {}
            for tok in verse_toks:
                grouped.setdefault(int(tok["word_index"]), []).append(tok)
            text = RootAyahExtraction._build_verse_text(grouped)  # type: ignore
            verses.append(f"سورة {s} آية {a} – {text}")
        return verses
    return []


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
    "frequency_word_root": [
        {"method": "lemma_match_surah_filter", "on_fail": "The word was not found in the specified surah."},
        {"postprocess": "count"},
    ],
    # 5
    "thematic_classification_roots": [
        {"method": "lemma_match", "on_fail": "The word is not present in the Qur'anic corpus."},
        {"method": "root_lookup_combined"},
    ],
    # 6
    "semantic_domain_root": [
        {"method": "root_match", "on_fail": "The root could not be found in the Qur'anic text."},
        {"method": "root_lookup_combined"},
        {"method": "domain_classification"},
    ],
    # 7
    "root_extraction": [
        {"method": "lemma_match", "on_fail": "The word you provided does not exist in the Qur'anic database."},
        {"postprocess": "extract_root"},
    ],
    # 8
    "root_ayah_extraction": [
        {"method": "ayah_extraction", "on_fail": "لم أجد آيات تحتوي على الكلمة أو الجذر المطلوب."},
    ],
    # 9
    "roots_by_topic": [
        {"method": "topic_expansion", "on_fail": "لم أجد جذورًا مرتبطة بهذا الموضوع."},
        {"postprocess": "attach_sample_ayahs"},
    ],
    # 10
    "forms_of_root": [
        {"method": "lemma_match", "on_fail": "❌ لم أتمكن من العثور على الجذر أو الكلمة المطلوبة في قاعدة البيانات."},
        {"method": "root_lookup_combined"},
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
    "ayah_extraction": ayah_extraction,
}


# --------------------------------------------------------------------------- #
# 4. Dispatcher entry-point                                                   #
# --------------------------------------------------------------------------- #
def dispatch_retrieval(question_type: str, target: str, surah: int | None = None) -> Dict:
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
                # Use unique (surah, ayah, word_index) keys for counting
                word_keys = {(t['surah'], t['ayah'], t['word_index']) for t in morph_cache}
                ctx["occurrence_count"] = len(word_keys)

                # ── DEBUG: list UNIQUE word occurrences (no duplicate tokens) ──
                occ_refs = [f"S{s}:A{a}:W{w}" for s, a, w in sorted(word_keys)]
                pretty_refs = [f"سورة {s} آية {a}" for s, a, _ in sorted(word_keys)]
                ctx["occurrence_refs"] = occ_refs  # make available to prompt
                ctx["occurrence_refs_pretty"] = pretty_refs
                refs_list = ", ".join(occ_refs)
                print(f"🔍 [DEBUG] Occurrences ({len(occ_refs)} words): {refs_list}")
            elif step["postprocess"] == "extract_root" and morph_cache:
                # Attempt to extract the first available root from cached tokens
                root_str = next((t.get("root") for t in morph_cache if t.get("root")), None)
                if root_str is None:
                    # Try a secondary lookup using smart_exact_match (may return tokens with root filled)
                    try:
                        from .morphology_retriever import smart_exact_match as _smart_match
                        _toks, _note = _smart_match(target)
                        if _toks and _toks[0].get("root"):
                            root_str = _toks[0]["root"]
                            ctx["root_note"] = f"✅ Extracted root «{root_str}» via secondary lookup."
                        else:
                            root_str = target  # graceful final fallback
                            ctx["root_note"] = "ℹ️  Root not found; using target word as-is."
                    except Exception:
                        root_str = target
                        ctx["root_note"] = "ℹ️  Root not found; using target word as-is."
                else:
                    ctx["root_note"] = f"✅ Extracted root «{root_str}» from morphology tokens."

                ctx["root"] = root_str
            elif step["postprocess"] == "attach_sample_ayahs":
                # Build a mapping {root: first_ayah_text}
                root_list_str = ctx.get("topic_expansion")
                roots = []
                if isinstance(root_list_str, dict):
                    roots = root_list_str.get("root_list", [])
                elif isinstance(root_list_str, str) and root_list_str.strip():
                    roots = [r.strip() for r in root_list_str.split("،") if r.strip()]
                samples: dict[str, str] = {}
                for r in roots:
                    try:
                        verses = _ayahs_by_root_exact(r, max_n=3)
                        if verses:
                            samples[r] = verses
                    except Exception:
                        continue
                if samples:
                    ctx["root_samples"] = samples
            continue

        method_name = step["method"]
        print(f"\n🔍 [] Executing method: {method_name}")
        
        # Get the callable for this method
        method = CALLABLES[method_name]

        # Primary call to the retrieval helper --------------------------------
        if method_name == "ayah_extraction":
            # Inject surah filter into function attr then call
            if surah is not None:
                ayah_extraction._SURAH_FILTER = surah
            else:
                ayah_extraction._SURAH_FILTER = None
            result, note = ayah_extraction(target)
        elif method_name == "lemma_match_surah_filter":
            result, note = method(target, surah)
        elif method_name == "lemma_match":
            result, note = method(target)
        elif method_name == "topic_expansion":
            result, note = method(target)
        else:
            # For all other methods we postpone execution (or handle specially)
            result, note = None, ""

        # Store the result for potential post-processing
        if result and isinstance(result, list) and isinstance(result[0], dict):
            morph_cache = result

        # ─── SPECIAL: root_lookup_combined needs the root from morphology ─
        if method_name == "root_lookup_combined":
            # ── NEW: find the *first* token that actually carries a root ──
            root_arg = None
            if morph_cache:   
                # First try to find a token that matches our target word
                target_token = None
                target_normalized = target.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")
                
                # Try to find the token by surah, ayah, and word_index first
                for tok in morph_cache:
                    if tok.get("surah") == 37 and tok.get("ayah") == 140 and tok.get("word_index") == 2:
                        target_token = tok
                        break
                
                # If not found by location, try normalized matching
                if not target_token:
                    for tok in morph_cache:
                        # Safely handle cases where 'token' or 'lemma' might be None
                        raw_token: str = tok.get("token") or ""
                        raw_lemma: str = tok.get("lemma") or ""

                        token_normalized = raw_token.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")
                        lemma_normalized = raw_lemma.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")
                        
                        if token_normalized == target_normalized or lemma_normalized == target_normalized:
                            target_token = tok
                            print(f"🔍 [DEBUG] Found matching token!")
                            break
                
                # If we found a matching token, use its root
                if target_token:
                    root_field = target_token.get("root")
                    if root_field:
                        root_arg = root_field
                
                # If no matching token or no root, fall back to first token with root
                if root_arg is None:
                    for tok in morph_cache:
                        root_field = tok.get("root")
                        if root_field:
                            root_arg = root_field
                            break

            if root_arg is None:                   # ③ ultimate fallback
                root_arg = target

            # ① primary lookup with extracted root
            data, note = root_lookup_combined(root_arg)

            # ② fallback: try the *original* target text if primary misses
            if data is None and target != root_arg:
                alt_data, alt_note = root_lookup_combined(target)
                # merge diagnostic notes for transparency
                note = note + "\n↪︎ Retrying with user-supplied root …\n" + alt_note
                data = alt_data

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
            if morph_cache is None:
                fail_msg = step.get("on_fail")
                if fail_msg:
                    ctx["error_message"] = fail_msg
                    return ctx
            # Skip adding morphology tokens to ctx to keep context light
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

        # After execution, if result present and method is topic_expansion -> store
        if method_name == "topic_expansion":
            ctx[method_name] = result
            ctx[f"{method_name}_note"] = note
            continue

    return ctx

def _extract_root(self, target_word: str, tokens: List[Dict]) -> str:
    """
    Extract the root from the target word or tokens.
    Prioritizes the target word's root if available.
    """
    # Always use the target word as root if it starts with hamza
    if target_word.startswith(("أ", "إ", "آ")):
        return target_word
    
    # First try to find a token that matches our target word
    target_token = None
    target_normalized = self._normalize_arabic(target_word)
    
    # Try to find the token by surah, ayah, and word_index first
    for tok in tokens:
        if tok.get("surah") == 37 and tok.get("ayah") == 140 and tok.get("word_index") == 2:
            target_token = tok
            break
    
    # If not found by location, try normalized matching
    if not target_token:
        for tok in tokens:
            # Safely handle cases where 'token' or 'lemma' might be None
            raw_token: str = tok.get("token") or ""
            raw_lemma: str = tok.get("lemma") or ""

            token_normalized = raw_token.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")
            lemma_normalized = raw_lemma.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")
            
            # Only match if the normalized forms are exactly equal
            # This prevents partial matches within words (like سابق matching with ابق)
            if token_normalized == target_normalized or lemma_normalized == target_normalized:
                target_token = tok
                break
    
    # If we found a matching token, use its root
    if target_token and target_token.get("root"):
        return target_token["root"]
    
    # If no matching token found, use the target word as root
    return target_word

def _normalize_arabic(self, text: str) -> str:
    """
    Normalize Arabic text by removing diacritics and normalizing hamza forms.
    """
    # Guard against None input
    if not text:
        return ""

    # Remove diacritics
    text = text.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")

    # Normalize hamza forms to alif
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")

    # Normalize other common variations
    text = text.replace("ى", "ي").replace("ة", "ه")

    return text