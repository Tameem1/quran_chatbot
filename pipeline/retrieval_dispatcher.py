# pipeline/retrieval_dispatcher.py
from services.retrievers.dispatcher import dispatch_retrieval


def retrieve_context(question_type: str, target: str) -> dict:
    """Stage 3 wrapper."""
    return dispatch_retrieval(question_type, target)