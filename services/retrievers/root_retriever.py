# services/retrievers/root_retriever.py
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from utils.paths import ROOT_ANALYSIS_FILE


def root_lookup_combined(
    root: str,
    analysis_path: str | Path = ROOT_ANALYSIS_FILE,
) -> Tuple[Optional[Dict], str]:
    """
    Locate an exact root in `root_analysis.jsonl` (Stage 3 helper).
    """
    p = Path(analysis_path)
    if not p.exists():
        return None, f"❗ root_analysis file not found: {p}"

    with p.open(encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line)
            entry_root = entry.get("root_stripped") or entry.get("root")
            if entry_root == root:
                return entry, f"✅ Root '{root}' found in root_analysis."

    return None, f"Root '{root}' not present in root_analysis."