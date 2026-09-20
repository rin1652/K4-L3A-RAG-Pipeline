"""Task 9 — hybrid retrieval và PageIndex fallback."""

import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


load_dotenv()

SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or 0.55)
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả hybrid/dense results, hoặc PageIndex khi dense thiếu tự tin."""
    if not query.strip() or top_k <= 0:
        return []

    dense = semantic_search(query, top_k=top_k * 2)
    if use_reranking:
        sparse = lexical_search(query, top_k=top_k * 2)
        results = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        results = dense[:top_k]

    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception:
            pass
    return results


if __name__ == "__main__":
    for result in retrieve("Đăng ký học phần kỳ 1 như thế nào?", top_k=3):
        print(f"{result['score']:.4f} | {result['retrieval_method']} | {result['id']}")