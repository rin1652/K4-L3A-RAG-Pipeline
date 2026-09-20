"""Task 4 — load Markdown, chunk, embed và index vào ChromaDB."""

import hashlib
import math
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_FINGERPRINT = hashlib.sha256(
    f"{EMBEDDING_PROVIDER}:{EMBEDDING_MODEL}".encode()
).hexdigest()[:12]
COLLECTION_NAME = f"rag_documents_{EMBEDDING_FINGERPRINT}"


@lru_cache(maxsize=1)
def _local_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed documents và query qua duy nhất provider/model đã cấu hình."""
    if not texts:
        return []
    if EMBEDDING_PROVIDER == "sentence_transformers":
        return _local_embedding_model().encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        ).tolist()
    if EMBEDDING_PROVIDER == "openai":
        from openai import OpenAI

        response = OpenAI().embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]
    if EMBEDDING_PROVIDER == "gemini":
        from google import genai

        response = genai.Client().models.embed_content(model=EMBEDDING_MODEL, contents=texts)
        return [item.values for item in response.embeddings]
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở persistent Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "embedding_provider": EMBEDDING_PROVIDER,
            "embedding_model": EMBEDDING_MODEL,
        },
    )


def load_documents() -> list[dict]:
    """Đọc Markdown theo thứ tự ổn định và giữ metadata nguồn."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        lines = content.splitlines()
        title = next(
            (line[2:].strip() for line in lines if line.startswith("# ")),
            path.stem.replace("-", " ").title(),
        )
        source_value = next(
            (line.split(":**", 1)[1].strip() for line in lines if line.startswith("**Source:**")),
            "",
        )
        relative_path = path.relative_to(STANDARDIZED_DIR).as_posix()
        documents.append(
            {
                "id": relative_path,
                "content": content,
                "metadata": {
                    "source": relative_path,
                    "title": title,
                    "doc_type": path.parent.name,
                    "url": source_value if source_value.startswith(("http://", "https://")) else None,
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia document thành chunks có ID ổn định và đúng thứ tự gốc."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", ". ", "\n", " ", ""],
    )
    chunks = []
    for document in documents:
        normalized = re.sub(r"(?<!\n)\n(?!\n)", " ", document["content"])
        for index, text in enumerate(splitter.split_text(normalized)):
            if text.strip():
                chunks.append(
                    {
                        "id": f"{document['id']}::chunk-{index}",
                        "content": text,
                        "metadata": {**document["metadata"], "chunk_index": index},
                    }
                )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk, không làm mất metadata."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected number of vectors")
    if vectors:
        dimension = len(vectors[0])
        if dimension == 0 or any(
            len(vector) != dimension
            or any(not math.isfinite(float(value)) for value in vector)
            for vector in vectors
        ):
            raise ValueError("Embedding provider returned invalid vectors")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Đồng bộ corpus chunks vào ChromaDB, không để ID cũ hoặc trùng."""
    if not chunks:
        raise ValueError("Cannot index an empty corpus")
    collection = get_collection()
    current_ids = set(collection.get()["ids"])
    new_ids = {chunk["id"] for chunk in chunks}
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[
            {key: value if value is not None else "" for key, value in chunk["metadata"].items()}
            for chunk in chunks
        ],
    )
    stale_ids = list(current_ids - new_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)


def run_pipeline() -> None:
    documents = load_documents()
    if not documents:
        raise RuntimeError(f"No Markdown documents found in {STANDARDIZED_DIR}")
    chunks = chunk_documents(documents)
    index_to_vectorstore(embed_chunks(chunks))
    print(f"Indexed {len(chunks)} chunks from {len(documents)} documents")


if __name__ == "__main__":
    run_pipeline()