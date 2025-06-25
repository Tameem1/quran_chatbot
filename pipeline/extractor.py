# pipeline/extractor.py
from services.extractors.quranic_word_extractor import extract_word, extract_two_words
from .classifier import classify_question_type


def extract_target_entities(question: str) -> str | tuple[str, str] | None:
    """Stage 2 wrapper."""
    # First classify the question to determine if it's a difference_two_words type
    question_type = classify_question_type(question)
    
    if question_type == "difference_two_words":
        # Extract two words for difference questions
        return extract_two_words(question)
    else:
        # Extract single word for other question types
        return extract_word(question)