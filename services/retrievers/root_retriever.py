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

    print(f"\n🔍 [DEBUG] Root lookup input: '{root}'")

    # Add debugging note about the root being searched
    debug_note = f"🔍 Searching for root '{root}' in root_analysis.jsonl"

    # Normalize the input root for comparison
    normalized_root = _normalize_root(root)
    print(f"🔍 [DEBUG] Normalized root: '{normalized_root}'")

    with p.open(encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line)
            entry_root = entry.get("root_stripped") or entry.get("root")
            # Normalize the entry root for comparison
            normalized_entry_root = _normalize_root(entry_root)
            
            if normalized_entry_root == normalized_root:
                # Add debugging note about the match found
                debug_note += f"\n✅ Found matching root '{root}' in entry #{entry.get('#', 'N/A')}"
                return entry, debug_note
            # Debug for our target root
            if entry_root == "أبق" or root == "أبق":
                print(f"\n🔍 [DEBUG] Found potential match:")
                print(f"🔍 [DEBUG] Entry root: '{entry_root}'")
                print(f"🔍 [DEBUG] Entry root type: {type(entry_root)}")
                print(f"🔍 [DEBUG] Entry root bytes: {entry_root.encode('utf-8')}")
                print(f"🔍 [DEBUG] Entry: {entry}")

    # Add debugging note about no match found
    debug_note += f"\n❌ No matching root found for '{root}' in root_analysis.jsonl"
    return None, debug_note

def _normalize_root(root: str) -> str:
    """
    Normalize a root by handling hamza forms and other variations.
    """
    # Normalize hamza forms to alif
    root = root.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    
    # Remove short-vowel diacritics (keep shadda)
    root = root.replace("َ", "").replace("ُ", "").replace("ِ", "").replace("ْ", "")
    
    # Normalize other common variations
    root = root.replace("ى", "ي").replace("ة", "ه")
    
    return root