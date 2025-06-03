# services/llm.py
"""
Thin wrapper around the OpenAI ChatCompletion endpoint
+ optional console-logging (prompt & word counts).

If the caller sets `verbose=True`, the function prints:
  • token-count estimate for the outgoing prompt
  • the full prompt in role:name format
  • length of the returned answer
"""

from __future__ import annotations

import json
import os
from typing import List, Dict

from openai import OpenAI

# --------------------------------------------------------------
# Configuration (override via env vars)
# --------------------------------------------------------------
_MODEL_DEFAULT = os.getenv("QURAN_LLM_MODEL", "gpt-4o-mini-2024-07-18")
_TIMEOUT       = int(os.getenv("QURAN_LLM_TIMEOUT", "30"))

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --------------------------------------------------------------
# Public helpers
# --------------------------------------------------------------
def default_model() -> str:         # used by the pipeline for log output
    return _MODEL_DEFAULT


def _pretty_messages(msgs: List[Dict]) -> str:
    """
    Human-friendly prompt display:
        system: <content>
        user  : <content>
        ...
    """
    return "\n".join(f"{m['role']}: {m['content']}" for m in msgs)


def query_llm(
    messages: List[Dict],
    *,
    model: str = _MODEL_DEFAULT,
    verbose: bool = False,
) -> str:
    """
    Make a single ChatCompletion call.
    When `verbose` is True we echo the outgoing prompt to stderr/console
    before sending, and the length of the answer afterwards.
    """
    if verbose:
        word_count = sum(len(m["content"].split()) for m in messages)
        print(f"[LLM] → sending prompt (~{word_count} words)")
        print("─────────────────────────────────────────────────────────")
        print(_pretty_messages(messages))
        print("─────────────────────────────────────────────────────────")

    rsp = _client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=512,
        temperature=0.2,
        timeout=_TIMEOUT,
    )

    answer = rsp.choices[0].message.content.strip()

    if verbose:
        print(f"[LLM] ← answer length {len(answer)} chars")

    return answer