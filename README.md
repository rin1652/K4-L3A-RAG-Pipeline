# HUST RAG Chatbot — Lab 08

Chatbot hỏi đáp có citation về quy chế đào tạo, đăng ký học phần, học phí và thông báo học vụ của Đại học Bách khoa Hà Nội. Pipeline sử dụng dense retrieval, BM25, Reciprocal Rank Fusion (RRF), PageIndex fallback và FPT AI Factory để sinh câu trả lời từ bằng chứng.

## Trạng thái

- 3 PDF chính sách + 6 bài viết công khai; 9 Markdown chuẩn hóa.
- 665 chunks, `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50`.
- Dense: `BAAI/bge-m3` + Chroma cosine.
- Lexical: BM25 trên cùng corpus chunks.
- Fusion: RRF gọi đúng một lần, `k=60`.
- Fallback threshold: cosine dense `0.50`.
- Generation: FPT AI Factory `DeepSeek-V4-Flash`, citation `[S#]` ánh xạ trực tiếp tới nguồn trên UI.
- Golden dataset: 18 câu; A/B dense-only và hybrid + RRF.

## Kiến trúc

```text
data/landing
  ├─ legal/*.pdf
  └─ news/*.json
        ↓ Task 3
 data/standardized/{legal,news}/*.md
        ↓ Task 4
 chunks 500/50 ── BGE-M3 ── Chroma cosine
        │
        ├─ Task 5: dense ─┐
        └─ Task 6: BM25 ──┴─ Task 7: RRF ──┐
                                              ├─ Task 9: retrieve
 dense cosine < 0.50 ── Task 8: PageIndex ──┘
        ↓
 Task 10: reorder context → DeepSeek-V4-Flash → answer + sources
```

PageIndex là dịch vụ tùy chọn cần `PAGEINDEX_API_KEY`. Nếu dịch vụ chưa cấu hình hoặc lỗi, pipeline bắt exception và giữ kết quả hybrid, không làm UI crash.

## Corpus

Nguồn legal:

- [Quy chế đào tạo HUST năm 2025](https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/QCDT_2025_5445_QD-DHBK.pdf)
- [Quy chế tổ chức và quản lý đào tạo năm 2024](https://sdh.hust.edu.vn/Upload/19/files/Quyche/2024/10_2%20Quy%20ch%E1%BA%BF%20TCQL%20%C4%90%C3%A0o%20t%E1%BA%A1o_2024_VP%C4%90H_final_%C4%91%C3%A3%20k%C3%BD.pdf)
- [Quy định ngoại ngữ sinh viên chính quy K71 năm 2026](https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/00_%20Quy%20%C4%91%E1%BB%8Bnh%20ngo%E1%BA%A1i%20ng%E1%BB%AF%20K71_final_%C4%91%C3%A3%20k%C3%BD.pdf)

Sáu bài viết trong `data/landing/news/` lấy từ cổng thông tin HUST và giữ đủ `url`, `title`, `date_crawled`, `content_markdown`. `data/landing/` giữ bản gốc; Task 4 chỉ đọc `data/standardized/`.

## Cài đặt

Yêu cầu Python 3.10–3.13, Git và Chromium của Playwright.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
copy .env.example .env
```

macOS/Linux dùng `source .venv/bin/activate` và `cp .env.example .env`.

Điền khóa cục bộ vào `.env`:

```env
LLM_PROVIDER=fpt
LLM_MODEL=DeepSeek-V4-Flash
FPT_BASE_URL=https://mkp-api.fptcloud.com
FPT_API_KEY=...
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-m3
SCORE_THRESHOLD=0.50
PAGEINDEX_API_KEY=...  # optional
```

Không commit `.env`, API key, `chroma_db/` hoặc cache PageIndex.

## Chạy pipeline

```powershell
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
python -m src.task5_semantic_search
python -m src.task6_lexical_search
python -m src.task7_reranking
```

Nếu có PageIndex key, upload/cache ba PDF một lần:

```powershell
python -m src.task8_pageindex_vectorless
```

Demo PageIndex đã được kiểm chứng với query `Sinh viên bị buộc thôi học khi nào?`: ba PDF được cache, kết quả đứng đầu là `Điều 19. Cảnh báo học tập và buộc thôi học`, `retrieval_method=pageindex`, trang 19. Có thể ép nhánh fallback khi demo mà không đổi cấu hình production bằng `retrieve(query, top_k=3, score_threshold=1.0)`. PageIndex hiện cảnh báo REST retrieval endpoint sẽ bị deprecate; parser hỗ trợ response `relevant_contents` dạng list lồng nhau của API hiện tại.

Với query ngoài domain, PageIndex có thể trả rỗng; Task 9 khi đó giữ hybrid result và Task 10 phải safe-refuse nếu không có bằng chứng. Đây là hành vi fail-safe theo contract.

Chạy giao diện:

```powershell
streamlit run app.py
```

Nếu Windows báo warning từ file watcher/torchvision:

```powershell
streamlit run app.py --server.fileWatcherType none
```

Lần đầu BGE-M3 được nạp/tải trên CPU có thể chậm. Những lần hỏi trong cùng tiến trình sẽ tái sử dụng model đã cache.

## Demo

Câu trong domain:

- `Thời gian đăng ký học phần học kỳ hè 2025-2026 là khi nào?`
- `Sinh viên được đăng ký tối đa bao nhiêu tín chỉ trong học kỳ hè?`
- `Điều kiện đăng ký chương trình thứ hai là gì?`

Câu ngoài domain:

- `Cách nấu phở bò truyền thống như thế nào?`
- `Thời tiết Hà Nội ngày mai thế nào?`

Ở `SCORE_THRESHOLD=0.50`, ba query trong domain dùng để hiệu chỉnh đạt cosine `0.7014–0.7514`; ba query ngoài domain đạt `0.3653–0.4327` và kích hoạt fallback.

## Đánh giá A/B

Kết quả trên commit code/corpus `9371c76`, cùng 18 câu, prompt, generator và `top_k=5`:

| Metric | Dense-only | Hybrid + RRF | Delta |
| --- | ---: | ---: | ---: |
| Faithfulness | 0.8721 | 0.9100 | +0.0379 |
| Answer relevance | 0.5660 | 0.6073 | +0.0413 |
| Context recall | 0.9762 | 0.9734 | -0.0028 |
| Context precision | 0.8111 | 0.8222 | +0.0111 |
| Average | 0.8064 | 0.8282 | +0.0219 |

Chi tiết cấu hình, latency, worst performers và root cause: [group_project/evaluation/RESULT.md](group_project/evaluation/RESULT.md).

Chạy lại evaluation chỉ khi đã cấu hình `FPT_API_KEY`:

```powershell
python -m group_project.evaluation.run_evaluation
```

Muốn chạy mới hoàn toàn, xóa nội dung cũ trong `evaluation_details.json` thành `[]`; runner có thể resume các case đã lưu.

## Kiểm thử

```powershell
pytest tests/test_contracts.py -q
pytest tests/test_acceptance.py -q
pytest -q
```

## Nhóm và báo cáo

- Thành viên và ownership: [TEAMMATES.md](TEAMMATES.md)
- Báo cáo cá nhân: [`reports/`](reports/)

Một repository dùng chung cho cả nhóm. Mỗi thành viên nộp cùng URL repository trên VLearn; đóng góp được đối chiếu bằng nhánh, commit, PR, test và báo cáo cá nhân.