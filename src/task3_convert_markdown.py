"""Task 3 — Chuẩn hóa PDF và JSON sang Markdown."""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .task1_collect_legal_docs import LEGAL_SOURCES


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOCX và thêm metadata nguồn."""
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    source_stems = {
        path.stem
        for path in legal_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".doc", ".docx"}
    }
    for stale in output_dir.glob("*.md"):
        if stale.stem not in source_stems:
            stale.unlink()

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        source = LEGAL_SOURCES.get(path.name, {})
        title = source.get("title", path.stem.replace("-", " ").title())
        url = source.get("url")
        content = converter.convert(str(path)).text_content.strip()
        if len(content) < 200:
            raise ValueError(f"Converted legal document is too short: {path}")
        header = (
            f"# {title}\n\n"
            f"**Source:** {url or path.name}\n\n"
            "**Document type:** legal\n\n---\n\n"
        )
        output = output_dir / f"{path.stem}.md"
        temporary = output.with_suffix(".md.tmp")
        temporary.write_text(header + content, encoding="utf-8")
        temporary.replace(output)
        print(f"Saved: {output}")


def convert_news_articles() -> None:
    """Convert JSON bài viết và giữ metadata nguồn."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    source_stems = {path.stem for path in news_dir.glob("*.json")}
    for stale in output_dir.glob("*.md"):
        if stale.stem not in source_stems:
            stale.unlink()
    required = {"url", "title", "date_crawled", "content_markdown"}

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = required - data.keys()
        if missing:
            raise ValueError(f"{path.name} missing fields: {sorted(missing)}")
        if any(not isinstance(data[key], str) or not data[key].strip() for key in required):
            raise ValueError(f"{path.name} has invalid metadata values")
        parsed_url = urlparse(data["url"])
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(f"{path.name} has invalid URL")
        try:
            datetime.fromisoformat(data["date_crawled"].replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"{path.name} has invalid date_crawled") from error
        if "\n" in data["title"] or "\r" in data["title"]:
            raise ValueError(f"{path.name} has invalid title")
        content = data["content_markdown"].strip()
        if len(content) < 200:
            raise ValueError(f"Article is too short: {path}")
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n"
            "**Document type:** news\n\n---\n\n"
        )
        output = output_dir / f"{path.stem}.md"
        temporary = output.with_suffix(".md.tmp")
        temporary.write_text(header + content, encoding="utf-8")
        temporary.replace(output)
        print(f"Saved: {output}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()