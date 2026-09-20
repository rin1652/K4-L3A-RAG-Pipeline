"""Task 6 — BM25 trên đúng corpus chunks đang lưu trong ChromaDB."""

import re

from .task4_chunking_indexing import get_collection


CORPUS: list[dict] = []
STOPWORDS = {
    "ai", "bao", "bị", "các", "có", "của", "cho", "đã", "đến", "được",
    "gì", "hay", "khi", "không", "là", "lúc", "một", "nào", "những", "ở",
    "phải", "sinh", "thì", "theo", "trong", "từ", "và", "vào", "về", "viên",
}
DOMAIN_STOPWORDS = {"học", "phần", "kỳ"}


def _tokenize(text: str) -> list[str]:
    words = [word for word in re.findall(r"\w+", text.casefold()) if word not in STOPWORDS]
    unigrams = [word for word in words if word not in DOMAIN_STOPWORDS]
    bigrams = [f"{left}_{right}" for left, right in zip(words, words[1:])]
    trigrams = ["_".join(words[index:index + 3]) for index in range(len(words) - 2)]
    return unigrams + bigrams + trigrams + trigrams


def _indexed_corpus() -> list[dict]:
    response = get_collection().get(include=["documents", "metadatas"])
    return sorted(
        (
            {"id": item_id, "content": content, "metadata": metadata}
            for item_id, content, metadata in zip(
                response["ids"], response["documents"], response["metadatas"]
            )
        ),
        key=lambda item: item["id"],
    )


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index với cùng tokenizer cho corpus và query."""
    from rank_bm25 import BM25Okapi

    return BM25Okapi([_tokenize(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not query.strip() or top_k <= 0:
        return []
    corpus = CORPUS or _indexed_corpus()
    if not corpus:
        return []
    query_tokens = _tokenize(query)
    query_terms = set(query_tokens)
    scores = build_bm25_index(corpus).get_scores(query_tokens)
    ranked = sorted(
        (
            (index, float(score), len(query_terms.intersection(_tokenize(corpus[index]["content"]))))
            for index, score in enumerate(scores)
            if query_terms.intersection(_tokenize(corpus[index]["content"]))
        ),
        key=lambda item: (item[1], item[2]),
        reverse=True,
    )[:top_k]
    return [
        {
            "id": corpus[index]["id"],
            "content": corpus[index]["content"],
            "score": score,
            "metadata": corpus[index]["metadata"],
            "retrieval_method": "bm25",
        }
        for index, score, _overlap in ranked
    ]


if __name__ == "__main__":
    for result in lexical_search("đăng ký học phần", top_k=3):
        print(f"{result['score']:.4f} | {result['id']}")