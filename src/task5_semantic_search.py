"""Task 5 — dense search trên ChromaDB bằng shared embedding function."""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo cosine similarity giảm dần."""
    if not query.strip() or top_k <= 0:
        return []
    collection = get_collection()
    count = collection.count() if hasattr(collection, "count") else top_k
    if count == 0:
        return []
    response = collection.query(
        query_embeddings=[embed_texts([query])[0]],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )
    results = [
        {
            "id": item_id,
            "content": content,
            "score": 1.0 - float(distance),
            "metadata": metadata,
            "retrieval_method": "dense",
        }
        for item_id, content, metadata, distance in zip(
            response["ids"][0],
            response["documents"][0],
            response["metadatas"][0],
            response["distances"][0],
        )
    ]
    return sorted(results, key=lambda item: item["score"], reverse=True)


if __name__ == "__main__":
    for result in semantic_search("Đăng ký học phần như thế nào?", top_k=3):
        print(f"{result['score']:.4f} | {result['id']}")