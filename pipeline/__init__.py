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

from typing import List, Dict, Callable, Optional, Union
import sys
from io import StringIO

from .classifier import classify_question_type
from .extractor import extract_target_entities
from .retrieval_dispatcher import retrieve_context
from .prompt_builder import build_prompt
from services.extractors.surah_extractor import extract_surah

from services.llm import query_llm, default_model


class QuranQAPipeline:
    """
    5-stage Quranic QA pipeline **with verbose console output**.
    """

    def __init__(self, *, verbose: bool = True, status_callback: Optional[Callable[[str], None]] = None):
        self.verbose = verbose
        self.status_callback = status_callback
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def _log(self, msg: str) -> None:
        """Log a message to both console and callback."""
        if self.verbose:
            formatted_msg = f"[Pipeline] {msg}\n"
            # Print to console
            print(formatted_msg, end='', flush=True)
            # Send to callback if available
            if self.status_callback:
                try:
                    self.status_callback(formatted_msg)
                except Exception as e:
                    print(f"Error in status callback: {e}", file=sys.stderr)

    def answer_question(self, question: str) -> str:
        """Process a question through the pipeline stages."""
        try:
            # Stage 1: Question Classification
            self._log(f"Received question: {question}")
            self._log("Stage-1 ▶️  Classifying question ...")
            q_type: str = classify_question_type(question)
            self._log(f"        ↳ Detected type  : {q_type}")

            # Stage 2: Target Entity Extraction
            self._log("Stage-2 ▶️  Extracting target entity ...")
            target: Union[str, tuple[str, str], None] = extract_target_entities(question)
            surah_num: int | None = extract_surah(question)

            if target is None:
                self._log("        ↳ Target entity  : ❓ NOT FOUND")
                return (
                    "❓ لم أستطع تحديد الكلمة أو الجذر المطلوب.\n"
                    "من فضلك وضّح الكلمة القرآنية التي تريد شرحها."
                )

            # Handle both single word and two-word cases
            if isinstance(target, tuple):
                word1, word2 = target
                self._log(f"        ↳ Target entities : {word1} و {word2}")
            else:
                self._log(f"        ↳ Target entity  : {target}")
                
            if surah_num is not None:
                self._log(f"        ↳ Surah filter   : S{surah_num}")

            # Stage 3: Context Retrieval
            self._log("Stage-3 ▶️  Retrieving context ...")
            
            # For difference_two_words, we need to handle two words
            if q_type == "difference_two_words" and isinstance(target, tuple):
                word1, word2 = target
                # Retrieve context for both words
                context1: Dict = retrieve_context(q_type, word1, surah_num)
                context2: Dict = retrieve_context(q_type, word2, surah_num)
                
                # Merge contexts, prefixing keys to distinguish between the two words
                context: Dict = {}
                for key, value in context1.items():
                    context[f"word1_{key}"] = value
                for key, value in context2.items():
                    context[f"word2_{key}"] = value
                    
                # Add the original words to context for prompt building
                context["word1"] = word1
                context["word2"] = word2
            else:
                # Handle single word case (existing logic)
                context: Dict = retrieve_context(q_type, target, surah_num)
                
            visible_keys = list(context.keys())
            self._log(f"        ↳ Context keys   : {visible_keys}")

            # ⚡ SPECIAL-CASE: for root_ayah_extraction we bypass the LLM and
            # return all extracted ayāt *verbatim* to avoid any loss.
            if q_type == "root_ayah_extraction":
                ayahs_list = context.get("ayah_extraction")
                if not ayahs_list:
                    return context.get("ayah_extraction_note", "❓ لم يتم العثور على آيات مطابقة.")

                # Optional: prepend count line
                count_line = f"✅ تم استخراج {len(ayahs_list)} آية:\n"
                bullet_lines = [f"• {v}" for v in ayahs_list]
                return count_line + "\n\n".join(bullet_lines)

            # Stage 4: Prompt Building
            self._log("Stage-4 ▶️  Building prompt ...")
            messages: List[Dict] = build_prompt(question, context, q_type)
            self._log("        ↳ Prompt built successfully")

            # Stage 5: LLM Query
            model_name = default_model()
            self._log(f"Stage-5 ▶️  Querying LLM ({model_name}) ...")
            answer: str = query_llm(messages, verbose=self.verbose)
            self._log("        ↳ LLM response received")

            return answer

        except Exception as e:
            error_msg = f"Error in pipeline: {str(e)}"
            self._log(error_msg)
            return f"❌ حدث خطأ أثناء معالجة السؤال: {str(e)}"