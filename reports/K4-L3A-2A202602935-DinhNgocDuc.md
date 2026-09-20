# Báo cáo đóng góp cá nhân

## Thông tin

- Họ và tên: Đinh Ngọc Đức
- Mã học viên: 2A202602935
- Nhóm/lớp: K4-L3A
- Repository/branch: `K4-L3A-RAG-Pipeline` / `DinhNgocDuc-2A202602935`

## Phần việc đã thực hiện

| Module/deliverable | Việc trực tiếp thực hiện | File/commit | Trạng thái |
| --- | --- | --- | --- |
| Data | Thu thập 3 PDF HUST và 6 bài công khai; làm sạch, chuẩn hóa Markdown có metadata | `src/task1_*`, `task2_*`, `task3_*`, `data/`; `6122db0` | Done |
| Retrieval | Chunk 500/50, ID ổn định, BGE-M3/Chroma cosine, BM25 cùng corpus | `src/task4_*` đến `task6_*`; `6122db0` | Done |
| Fusion/fallback | RRF không mutate, dùng dense cosine cho threshold; sửa parser PageIndex nested response và demo cloud | `src/task7_*` đến `task9_*`; `6122db0` và bản tích hợp sau `bf235f5` | Done |
| Generation/UI | FPT DeepSeek-V4-Flash, safe refusal, citation và source score/method; giữ sources theo score khi reorder context | `src/task10_generation.py`, `app.py`; `6122db0`, `9371c76` | Done |
| Evaluation | 18 golden cases; chạy 36 lượt A/B; bốn metric, worst performers và root cause | `group_project/evaluation/`; working tree sau `9371c76` | Done |
| Testing | Contract, acceptance, regression citation order và toàn bộ test | `tests/`; `9371c76` | Done |

## Quyết định kỹ thuật quan trọng

1. **Dùng một hàm `embed_texts()` cho index và query.**  
   **Evidence:** Task 4 và Task 5 cùng BGE-M3/fingerprint collection; tránh lệch model hoặc dimension.  
   **Trade-off:** chất lượng tiếng Việt tốt nhưng lần nạp đầu trên CPU chậm.

2. **Tách thứ tự context khỏi thứ tự sources.**  
   **Evidence:** commit `9371c76` giữ sources giảm dần theo score, gắn nhãn citation theo rank gốc rồi mới reorder context. Regression test xác nhận `[S#]` vẫn map đúng.  
   **Trade-off:** context có metadata nội bộ `_citation_index`, nhưng field này chỉ tồn tại trên bản sao và không rò vào output.

## Kiểm thử và kết quả

- `pytest tests/test_contracts.py -q`: pass.
- `pytest tests/test_acceptance.py -q`: pass.
- `pytest -q`: 30 tests pass sau thay đổi Task 10.
- Threshold calibration tại `0.50`: ba query in-domain có cosine `0.7014–0.7514`; ba query out-of-domain có `0.3653–0.4327`.
- A/B mới: average dense-only `0.8064`, hybrid + RRF `0.8282`; delta `+0.0219`.
- Lỗi đã phát hiện: reorder context từng làm nguồn UI không còn theo score; sửa bằng cách giữ danh sách sources gốc và chỉ reorder bản sao có nhãn cố định.

## Hạn chế

- PageIndex REST retrieval endpoint đã hoạt động nhưng có cảnh báo deprecation; cần theo dõi API kế nhiệm.
- Metric evaluation là lexical proxy có thể phạt paraphrase đúng; chưa dùng LLM judge/RAGAS.
- Một số định nghĩa và thủ tục vẫn bị chia qua ranh giới chunk; hướng cải thiện là adjacent-chunk expansion có đo lại precision.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh phần việc có thể đối chiếu bằng file, commit, test và artifact evaluation trong repository.

- Ngày: 20/09/2026
- Thành viên: Đinh Ngọc Đức