# pipeline/classifier.py
from services.classification import classify


def classify_question_type(question: str) -> str:
    """Stage 1 wrapper."""
    return classify(question)