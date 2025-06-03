# utils/arabic.py   (only the strip_diacritics function changed)

from __future__ import annotations
import unicodedata

_AR_REMAP = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",      # alif/hamza variants
        "ى": "ي", "ئ": "ي",                          # alif-maqṣūra + hamza-yah
        "ؤ": "و", "ـ": "",                           # tatwīl
    }
)

# ──────────────────────────────────────────────────────────────
def strip_diacritics(text: str) -> str:
    """
    Remove all Arabic diacritics **except** that we *promote*
    U+0670 (◌ٰ superscript alif = الألف الخنجرية) to a *real* alif.
    """
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text):
        if ch == "\u0670":            # ◌ٰ dagger-alif
            out.append("ا")           # keep it as a full alif
        elif unicodedata.combining(ch):
            continue                  # drop all other diacritics
        else:
            out.append(ch)
    return "".join(out)


def normalize(text: str) -> str:
    """Full normalisation: strip diacritics, map hamza/alif variants, trim."""
    return strip_diacritics(text).translate(_AR_REMAP).strip()