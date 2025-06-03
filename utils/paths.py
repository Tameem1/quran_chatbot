# utils/paths.py
"""
Centralised, import-safe file-system paths.
Adjust DATA_DIR if you relocate JSONL resources.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MORPHOLOGY_FILE = DATA_DIR / "quran_morphology.jsonl"
ROOT_ANALYSIS_FILE = DATA_DIR / "root_analysis.jsonl"
DICTIONARY_FILE = DATA_DIR / "arabic_dictionary.jsonl"