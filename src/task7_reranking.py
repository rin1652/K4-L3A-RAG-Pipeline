"""Task 7 — Reciprocal Rank Fusion cho dense và BM25."""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists theo ID mà không sửa item đầu vào."""
    if top_k <= 0:
        return []
    if k < 0:
        raise ValueError("k must be non-negative")

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked_list in ranked_lists:
        seen = set()
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            if item_id in seen:
                raise ValueError(f"Duplicate ID in ranked list: {item_id}")
            seen.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1 / (k + rank)
            items.setdefault(item_id, item)

    ranked_ids = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [
        {
            **items[item_id],
            "score": scores[item_id],
            "retrieval_method": "hybrid",
        }
        for item_id in ranked_ids
    ]


if __name__ == "__main__":
    dense = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.8}]
    bm25 = [{"id": "b", "score": 8.0}, {"id": "c", "score": 7.0}]
    print([(item["id"], item["score"]) for item in rerank_rrf([dense, bm25])])