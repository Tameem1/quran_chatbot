"""
Stage-2 helper – detect if the user mentions a specific Sūrah.

Return:
    • int in range 1‥114  – Qurʾānic chapter number
    • None                 – no chapter reference detected
"""
from __future__ import annotations

import re
from typing import Optional

from utils.arabic import normalize

# --------------------------------------------------------------------------- #
# Mapping: Arabic sūrah names → index (1-based)                               #
# --------------------------------------------------------------------------- #
# NOTE: we keep the *original* orthography then build a **normalised** lookup
# table at import-time so that all hamza/diacritic variants match reliably.
_SURAH_NAMES: list[str] = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف",
    "الأنفال", "التوبة", "يونس", "هود", "يوسف", "الرعد", "إبراهيم", "الحجر",
    "النحل", "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون",
    "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبإ", "فاطر", "يس", "الصافات", "ص", "الزمر",
    "غافر", "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد",
    "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم", "القمر", "الرحمن",
    "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة", "الصف", "الجمعة",
    "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة",
    "المعارج", "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان",
    "المرسلات", "النبأ", "النازعات", "عبس", "التكوير", "الانفطار", "المطففين",
    "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة",
    "الزلزلة", "العاديات", "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل",
    "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص",
    "الفلق", "الناس",
]

# Build a normalised dict for quick lookup.
_SURAH_NORM_TO_NUM: dict[str, int] = {normalize(name): i + 1 for i, name in enumerate(_SURAH_NAMES)}

# --------------------------------------------------------------------------- #
# Regex patterns                                                              #
# --------------------------------------------------------------------------- #
# Pattern for: "سورة البقرة" or "سوره البقرة" or "سورة 55"
_SURAH_PAT = re.compile(r"(?:سورة|سوره)\s+([^\s.,،؟?]+)")

# Arabic-Indic digits: \u0660–\u0669  • Western digits: 0–9
_DIGITS_PAT = re.compile("^[0-9\u0660-\u0669]+$")


def _arabic_digits_to_int(txt: str) -> Optional[int]:
    """Convert either Western or Arabic-Indic digits to int."""
    # Map Arabic-Indic digits to ASCII
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    try:
        return int(txt.translate(trans))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #

def extract_surah(question: str) -> Optional[int]:
    """Return a sūrah number if the question explicitly names one.

    Examples recognised:
      • "كم مرة وردت كلمة صبر في سورة البقرة؟"   -> 2
      • "في سورة 55، ماذا تعني كلمة الرحمن؟"     -> 55
    """
    m = _SURAH_PAT.search(question)
    if not m:
        return None

    raw = m.group(1).strip(" ‏\u200f")  # trim NBSP/RTL marks

    # case 1: digits
    if _DIGITS_PAT.match(raw):
        num = _arabic_digits_to_int(raw)
        if num and 1 <= num <= 114:
            return num
        return None

    # case 2: name → numeric index via normalised mapping
    key = normalize(raw)
    # Handle optional leading definite article
    if not key.startswith("ال"):
        key_alt = normalize("ال" + raw)
        num = _SURAH_NORM_TO_NUM.get(key_alt)
        if num:
            return num
    return _SURAH_NORM_TO_NUM.get(key) 