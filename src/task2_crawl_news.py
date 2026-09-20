"""Task 2 — Crawl thông báo hiện hành về đăng ký học tập HUST."""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

ARTICLE_SOURCES = {
    "ke-hoach-dang-ky-lop-2026-1": {
        "title": "Kế hoạch mở đăng ký lớp kỳ 1 năm học 2026-2027",
        "url": "https://ctt.hust.edu.vn/DisplayWeb/DisplayKehoach?kehoach=29240",
    },
    "dang-ky-ke-hoach-hoc-tap-2026-1": {
        "title": "Đăng ký kế hoạch học tập kỳ 1 năm học 2026-2027",
        "url": "https://ctt.hust.edu.vn/DisplayWeb/DisplayKehoach?kehoach=27235",
    },
    "su-co-he-thong-dang-ky-2026": {
        "title": "Thông báo về sự cố hệ thống đăng ký học tập",
        "url": "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=51623",
    },
    "ke-hoach-dang-ky-lop-he-2025-2026": {
        "title": "Kế hoạch mở đăng ký lớp học kỳ hè 2025-2026",
        "url": "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=50621",
    },
    "hoc-phi-ky-he-2025-2026": {
        "title": "Thông báo học phí kỳ hè năm học 2025-2026",
        "url": "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=51626",
    },
    "tiep-nhan-tro-lai-hoc-2026-1": {
        "title": "Tiếp nhận trở lại học kỳ hè và kỳ 1 năm học 2026-2027",
        "url": "https://ctt.hust.edu.vn/DisplayWeb/DisplayKehoach?kehoach=28237",
    },
}


def clean_markdown(markdown: str) -> str:
    """Bỏ chrome trang, thông tin liên hệ cá nhân và Markdown bị phân mảnh."""
    lines = markdown.splitlines()
    start = next((i for i, line in enumerate(lines) if line.lstrip().startswith("#")), 0)
    end = next(
        (i for i, line in enumerate(lines[start:], start) if "Bản quyền thuộc" in line),
        len(lines),
    )
    cleaned = []
    for line in lines[start:end]:
        if EMAIL_PATTERN.search(line):
            continue
        line = re.sub(r"(?<=[^\W\d_])\*{4}(?=[^\W\d_])", " ", line)
        cleaned.append(line.replace("****", ""))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()


async def crawl_article(url: str) -> dict:
    """Crawl một trang và trả đúng bốn field bắt buộc."""
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
    if not result.success:
        raise RuntimeError(result.error_message or f"Failed to crawl {url}")

    raw_markdown = getattr(result.markdown, "raw_markdown", result.markdown)
    markdown = clean_markdown(str(raw_markdown))
    if len(markdown) < 200:
        raise ValueError(f"Crawled content is too short: {url}")

    source = next(item for item in ARTICLE_SOURCES.values() if item["url"] == url)
    return {
        "url": url,
        "title": source["title"],
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON ổn định."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    articles = {}
    for slug, source in ARTICLE_SOURCES.items():
        try:
            articles[slug] = await crawl_article(source["url"])
        except Exception as error:
            print(f"Failed: {source['url']} — {error}")

    if len(articles) < 5:
        raise RuntimeError(f"Only {len(articles)} articles crawled; keeping previous snapshot")

    for slug, article in articles.items():
        output = DATA_DIR / f"{slug}.json"
        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(output)
        print(f"Saved: {output}")
    for slug in ARTICLE_SOURCES.keys() - articles.keys():
        (DATA_DIR / f"{slug}.json").unlink(missing_ok=True)

if __name__ == "__main__":
    asyncio.run(crawl_all())