# pipeline/prompt_builder.py
from datetime import datetime
from typing import Dict, List, Optional


def build_prompt(
    question: str,
    context: Dict,
    question_type: Optional[str] = None,   # ← NEW
) -> List[Dict]:
    """
    Stage-4 – construct chat prompt.
    If the question type is 'semantic_context_word', add an
    instruction to perform  التحليل الدلالي للكلمة ضمن السياق القرآني.
    """
    extra = ""
    if question_type == "semantic_context_word":
        extra = (
            "\nركّز على التحليل الدلالي للكلمة ضمن السياق القرآني "
            "الذي ظهرت فيه."
        )

    system_msg = (
        "You are a meticulous Quranic linguistics assistant. "
        "Answer strictly from <context/>, citing nothing else. "
        "If the answer is absent, say you do not know."
        f"{extra}\nUTC-timestamp: {datetime.utcnow().isoformat(timespec='seconds')}"
    )

    ctx_str = "\n".join(f"{k}: {v}" for k, v in context.items() if v)

    user_msg = (
        f"<question>\n{question}\n</question>\n"
        f"<context>\n{ctx_str}\n</context>"
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]