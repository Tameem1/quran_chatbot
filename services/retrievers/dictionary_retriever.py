# services/retrievers/dictionary_retriever.py
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from utils.arabic import normalize
from utils.paths import DICTIONARY_FILE


def lookup_definition(word: str) -> Tuple[Optional[Dict], str]:
    """
    Load a plain Arabic dictionary dump (JSONL) and return the entry.
    """
    f = Path(DICTIONARY_FILE)
    if not f.exists():
        return None, f"❗ Dictionary file not found: {f}"

    w_norm = normalize(word)
    with f.open(encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line)
            if normalize(entry.get("word", "")) == w_norm:
                return entry, f"✅ Definition for '{word}' found."

    return None, f"Definition for '{word}' not found."