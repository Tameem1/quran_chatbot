import json
from pathlib import Path
from typing import Dict, Tuple, Optional

def root_lookup_combined(
    root: str,
    analysis_path: str | Path
) -> Tuple[Optional[Dict], str]:
    """
    Retrieve the complete row for `root` from root_analysis.jsonl.

    Parameters
    ----------
    root : str
        Exact root string obtained from Quran Morphology (already normalised).
    analysis_path : str | Path
        Path to root_analysis JSON-Lines file (one JSON object per line).

    Returns
    -------
    (entry_dict | None, message_str)
        If found: the full dictionary row + success note.
        If not:  None + explanatory message (for the pipeline's `on_fail`).
    """
    file_path = Path(analysis_path)
    if not file_path.exists():
        return None, f"❗ root_analysis file not found at: {file_path}"

    with file_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line)

            # Prefer the 'root_stripped' field; fall back to 'root'
            entry_root = entry.get("root_stripped") or entry.get("root")

            if entry_root == root:
                return entry, f"✅ Root '{root}' located in root_analysis."

    # No match encountered
    return None, (
        f"The root '{root}' is not present in the root_analysis database."
    )

# ─── Example quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    data, note = root_lookup_combined("بتك", "/Users/tameem/Documents/ai-quran-research-assistant/chatbot/clean_data/root_analysis.jsonl")
    print(note)
    print(data)
    if data:
        print("Definition:", data.get("مفردات لسان العرب"))
        print("Synonyms:", data.get("المرادفات"))
        print("Antonyms:", data.get("الأضداد"))
        print("الفرق الدلالي:", data.get("الفرق الدلالي مع مرادف على الأقل"))
