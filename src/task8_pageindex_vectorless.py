"""Task 8 — PageIndex Cloud vectorless fallback có cache và timeout."""

import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from .task1_collect_legal_docs import LEGAL_SOURCES


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
ROOT_DIR = Path(__file__).parent.parent
LEGAL_DIR = ROOT_DIR / "data" / "landing" / "legal"
CACHE_FILE = ROOT_DIR / "pageindex_doc_ids.json"
BASE_URL = "https://api.pageindex.ai"
HTTP_TIMEOUT = 60
RETRIEVAL_TIMEOUT = 120


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def _save_cache(cache: dict) -> None:
    temporary = CACHE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(CACHE_FILE)


def _request(method: str, path: str, **kwargs) -> dict:
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY is not configured")
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers={"api_key": PAGEINDEX_API_KEY},
        timeout=HTTP_TIMEOUT,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


def upload_documents() -> None:
    """Upload PDF mới/thay đổi và cache doc_id theo checksum."""
    cache = _load_cache()
    for path in sorted(LEGAL_DIR.glob("*.pdf")):
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        cached = cache.get(path.name, {})
        if cached.get("sha256") == checksum and cached.get("doc_id"):
            print(f"Cached: {path.name}")
            continue
        with path.open("rb") as document:
            result = _request(
                "POST",
                "/doc/",
                files={"file": (path.name, document, "application/pdf")},
                data={"if_retrieval": "true"},
            )
        doc_id = result.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            raise RuntimeError(f"PageIndex did not return doc_id for {path.name}")
        cache[path.name] = {"doc_id": doc_id, "sha256": checksum}
        _save_cache(cache)
        print(f"Uploaded: {path.name}")


def _retrieve_document(doc_id: str, query: str) -> list[dict]:
    submitted = _request(
        "POST",
        "/retrieval/",
        json={"doc_id": doc_id, "query": query, "thinking": False},
    )
    retrieval_id = submitted.get("retrieval_id")
    if not isinstance(retrieval_id, str) or not retrieval_id:
        raise RuntimeError("PageIndex did not return retrieval_id")

    deadline = time.monotonic() + RETRIEVAL_TIMEOUT
    while time.monotonic() < deadline:
        result = _request("GET", f"/retrieval/{retrieval_id}/")
        status = result.get("status")
        if status == "completed":
            return result.get("retrieved_nodes") or []
        if status in {"failed", "error"}:
            raise RuntimeError(f"PageIndex retrieval failed: {result}")
        time.sleep(1)
    raise TimeoutError(f"PageIndex retrieval timed out after {RETRIEVAL_TIMEOUT}s")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Query cached PageIndex documents và parse thành SearchResult."""
    if not query.strip() or top_k <= 0:
        return []
    cache = _load_cache()
    if not cache:
        raise RuntimeError("No cached PageIndex documents; run upload_documents() first")

    results = []
    seen = set()
    for source, entry in sorted(cache.items()):
        doc_id = entry.get("doc_id") if isinstance(entry, dict) else entry
        if not doc_id:
            continue
        for node in _retrieve_document(str(doc_id), query):
            title = str(node.get("title") or Path(source).stem)
            contents = node.get("relevant_contents") or []
            if isinstance(contents, dict):
                contents = [contents]
            contents = [
                item
                for group in contents
                for item in (group if isinstance(group, list) else [group])
            ]
            for relevant in contents:
                if not isinstance(relevant, dict):
                    continue
                content = str(
                    relevant.get("relevant_content")
                    or relevant.get("content")
                    or ""
                ).strip()
                if not content:
                    continue
                digest = hashlib.sha1(content.encode()).hexdigest()[:12]
                item_id = f"pageindex::{doc_id}::{digest}"
                if item_id in seen:
                    continue
                seen.add(item_id)
                page = relevant.get(
                    "page_index",
                    relevant.get("physical_index", node.get("page_index", len(results))),
                )
                if isinstance(page, str):
                    match = re.search(r"\d+", page)
                    page = int(match.group()) if match else len(results)
                source_info = LEGAL_SOURCES.get(source, {})
                results.append(
                    {
                        "id": item_id,
                        "content": content,
                        "score": 1.0 / (len(results) + 1),
                        "metadata": {
                            "source": source,
                            "title": title,
                            "doc_type": "legal",
                            "url": source_info.get("url"),
                            "chunk_index": page if isinstance(page, int) and page >= 0 else len(results),
                        },
                        "retrieval_method": "pageindex",
                    }
                )
                if len(results) >= top_k:
                    return results
    return results


if __name__ == "__main__":
    upload_documents()