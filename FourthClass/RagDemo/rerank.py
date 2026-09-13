from collections.abc import Sequence

from sentence_transformers import CrossEncoder


RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


def rerank_documents(
    question: str,
    documents: Sequence,
    reranker: CrossEncoder,
    top_k: int,
) -> list:
    pairs = [(question, document.page_content) for document in documents]
    scores = reranker.predict(pairs)
    ranked_documents = sorted(
        zip(scores, documents),
        key=lambda item: item[0],
        reverse=True,
    )
    return [document for _, document in ranked_documents[:top_k]]