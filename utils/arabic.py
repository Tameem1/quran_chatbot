# utils/arabic.py   (only the strip_diacritics function changed)

from __future__ import annotations
import unicodedata

_AR_REMAP = str.maketrans(
    {
        "إ": "ا", "آ": "ا", "ٱ": "ا",      # alif/hamza variants (except أ)
        "ى": "ي", "ئ": "ي",                # alif-maqṣūra + hamza-yah
        "ؤ": "و", "ـ": "",                 # tatwīl
    }
)

# ──────────────────────────────────────────────────────────────
def strip_diacritics(text: str) -> str:
    """
    Remove all Arabic diacritics **except**:
      • U+0670 (◌ٰ dagger-alif) which we *promote* to a real alif
      • U+0651 (◌ّ  shadda) which we now *retain* intact.
    """
    if not text:
        return ""
        
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text):
        if ch == "\u0670":            # ◌ٰ dagger-alif
            out.append("ا")           # keep it as a full alif
        elif ch == "\u0651":          # ّ shadda
            out.append(ch)            # KEEP shadda
        elif unicodedata.combining(ch):
            continue                  # drop all other diacritics
        else:
            out.append(ch)
    result = "".join(out)
    return result


def normalize(text: str) -> str:
    """Full normalisation: strip diacritics, map hamza/alif variants, trim."""
    if not text:
        return ""
        
    # First strip diacritics
    text = strip_diacritics(text)
    
    # Then handle hamza forms
    # For words starting with hamza, keep the hamza form
    if text.startswith(("أ", "إ", "آ")):
        # Only normalize the hamza if it's not at the start
        text = text[0] + text[1:].translate(_AR_REMAP)
    else:
        # For other words, normalize all hamza forms
        text = text.translate(_AR_REMAP)
    
    return text.strip()