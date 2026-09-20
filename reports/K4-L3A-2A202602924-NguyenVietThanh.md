# Báo cáo đóng góp cá nhân

## Thông tin

- Họ và tên: Nguyễn Việt Thành
- Mã học viên: 2A202602924
- Nhóm/lớp: K4-L3A
- Vai trò: Generation & Streamlit UI
- Nhánh: `NguyenVietThanh-2A202602924`

## Phần việc/ownership

| Module/deliverable | Nội dung phụ trách | Artifact tích hợp | Trạng thái |
| --- | --- | --- | --- |
| Generation | Prompt chỉ trả lời từ context, safe refusal, dispatch FPT DeepSeek-V4-Flash | `src/task10_generation.py` | Done |
| Citation | Context có title/source/URL; nhãn `[S#]` ánh xạ đúng sources | `src/task10_generation.py`, `tests/test_generation.py` | Done |
| UI | Hiển thị answer, source, method, score, URL và lịch sử hội thoại | `app.py` | Done |
| Demo | Kiểm tra câu trong domain và ngoài domain không làm UI crash | README mục Demo | Done |

## Quyết định kỹ thuật

- Giữ `sources` theo score giảm dần; chỉ reorder bản sao context để giảm lost-in-the-middle.
- Nếu model trả citation ngoài phạm vi hoặc thiếu bằng chứng, trả safe refusal và `sources=[]`.

## Kiểm thử

- Regression test xác nhận source order và citation label không lệch.
- Contract và full suite pass trên bản tích hợp nhóm.

## Hạn chế

- FPT AI Factory là OpenAI-compatible provider; cần giữ đúng model/base URL trong `.env` cục bộ.
- Latency lần đầu chịu chi phí nạp embedding model và độ trễ provider.

## Xác nhận

Ownership trên được đối chiếu bằng artifact nhóm. Nhánh/commit cá nhân cần được giữ trên remote để giảng viên xác minh lịch sử đóng góp.

- Ngày: 20/09/2026
- Thành viên: Nguyễn Việt Thành