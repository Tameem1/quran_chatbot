# pipeline/__init__.py
"""
High-level orchestration + console logging.

Example run:
    $ python main.py "كم مرة ورد جذر سجد في القرآن؟"

Output:
    [Pipeline] Received question: كم مرة ورد جذر سجد في القرآن؟
    [Pipeline] Stage-1 ▶️  Classifying question ...
    [Pipeline]         ↳ Detected type  : frequency_word_root
    [Pipeline] Stage-2 ▶️  Extracting target entity ...
    [Pipeline]         ↳ Target entity  : سجد
    [Pipeline] Stage-3 ▶️  Retrieving context ...
    [Pipeline]         ↳ Context keys   : ['morphology_note', 'morphology', 'root_note']
    [Pipeline] Stage-4 ▶️  Building prompt ...
    [Pipeline] Stage-5 ▶️  Querying LLM (gpt-4o-mini-2024-07-18) ...
    [Pipeline]         ↳ LLM response received.
    … <final answer printed by main.py> …
"""

from __future__ import annotations

from typing import List, Dict

from .classifier import classify_question_type
from .extractor import extract_target_entities
from .retrieval_dispatcher import retrieve_context
from .prompt_builder import build_prompt

from services.llm import query_llm, default_model


class QuranQAPipeline:
    """
    5-stage Quranic QA pipeline **with verbose console output**.
    """

    def __init__(self, *, verbose: bool = True):
        self.verbose = verbose

    # ---------- private helper ------------------------------------ #
    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[Pipeline] {msg}")

    # ---------- public API ---------------------------------------- #
    def answer_question(self, question: str) -> str:
        self._log(f"Received question: {question}")

        # ── Stage 1 ────────────────────────────────────────────────
        self._log("Stage-1 ▶️  Classifying question ...")
        q_type: str = classify_question_type(question)
        self._log(f"        ↳ Detected type  : {q_type}")

        # ── Stage 2 ────────────────────────────────────────────────
        self._log("Stage-2 ▶️  Extracting target entity ...")
        target: str | None = extract_target_entities(question)
        if target is None:
            self._log("        ↳ Target entity  : ❓ NOT FOUND")
            return (
                "❓ لم أستطع تحديد الكلمة أو الجذر المطلوب.\n"
                "من فضلك وضّح الكلمة القرآنية التي تريد شرحها."
            )
        self._log(f"        ↳ Target entity  : {target}")

        # ── Stage 3 ────────────────────────────────────────────────
        self._log("Stage-3 ▶️  Retrieving context ...")
        context: Dict = retrieve_context(q_type, target)
        visible_keys = list(context.keys())
        self._log(f"        ↳ Context keys   : {visible_keys}")

        # ── Stage 4 ────────────────────────────────────────────────
        self._log("Stage-4 ▶️  Building prompt ...")
        messages: List[Dict] = build_prompt(question, context, q_type)

        # ── Stage 5 ────────────────────────────────────────────────
        model_name = default_model()  # small helper (see below)
        self._log(f"Stage-5 ▶️  Querying LLM ({model_name}) ...")
        answer: str = query_llm(messages, verbose=self.verbose)
        self._log("        ↳ LLM response received.")

        return answer