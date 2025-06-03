# pipeline/extractor.py
from services.extractors.quranic_word_extractor import extract_word


def extract_target_entities(question: str) -> str | None:
    """Stage 2 wrapper."""
    return extract_word(question)