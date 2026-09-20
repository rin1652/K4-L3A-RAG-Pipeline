"""Task 1 — Tải tài liệu chính sách/quy định HUST."""

from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

LEGAL_SOURCES = {
    "quy-che-dao-tao-2025.pdf": {
        "title": "Quy chế đào tạo của Đại học Bách khoa Hà Nội năm 2025",
        "url": "https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/QCDT_2025_5445_QD-DHBK.pdf",
    },
    "quy-che-to-chuc-quan-ly-dao-tao-2024.pdf": {
        "title": "Quy chế tổ chức và quản lý đào tạo năm 2024",
        "url": "https://sdh.hust.edu.vn/Upload/19/files/Quyche/2024/10_2%20Quy%20ch%E1%BA%BF%20TCQL%20%C4%90%C3%A0o%20t%E1%BA%A1o_2024_VP%C4%90H_final_%C4%91%C3%A3%20k%C3%BD.pdf",
    },
    "quy-dinh-ngoai-ngu-k71-2026.pdf": {
        "title": "Quy định về ngoại ngữ đối với sinh viên chính quy K71 năm 2026",
        "url": "https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/00_%20Quy%20%C4%91%E1%BB%8Bnh%20ngo%E1%BA%A1i%20ng%E1%BB%AF%20K71_final_%C4%91%C3%A3%20k%C3%BD.pdf",
    },
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải và xác thực ba PDF chính thức."""
    setup_directory()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HUST-RAG-Lab/1.0)"}
    downloaded = {}
    for filename, source in LEGAL_SOURCES.items():
        response = requests.get(source["url"], headers=headers, timeout=60)
        response.raise_for_status()
        content = response.content
        if len(content) <= 1024 or not content.startswith(b"%PDF"):
            raise ValueError(f"Invalid PDF response: {source['url']}")
        downloaded[filename] = content

    for filename, content in downloaded.items():
        output = DATA_DIR / filename
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(output)
        print(f"Saved: {output}")

    managed_extensions = {".pdf", ".doc", ".docx"}
    for stale in DATA_DIR.iterdir():
        if (
            stale.is_file()
            and stale.suffix.lower() in managed_extensions
            and stale.name not in LEGAL_SOURCES
        ):
            stale.unlink()
            print(f"Removed stale: {stale}")


if __name__ == "__main__":
    download_documents()