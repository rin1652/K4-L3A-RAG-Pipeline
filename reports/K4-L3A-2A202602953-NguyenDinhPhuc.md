# Báo cáo đóng góp cá nhân

## Thông tin

- Họ và tên: Nguyễn Đình Phúc
- Mã học viên: 2A202602953
- Nhóm/lớp: K4-L3A
- Vai trò: Team Lead; Integration & Delivery
- Nhánh: `NguyenDinhPhuc-2A202602953`

## Phần việc/ownership

| Module/deliverable | Nội dung phụ trách | Artifact tích hợp | Trạng thái |
| --- | --- | --- | --- |
| Planning | Chốt phạm vi HUST, chia ownership và kiểm soát interface giữa 10 task | `TEAMMATES.md`, `docs/MODULE_CONTRACTS.md` | Done |
| Integration | Kiểm tra dense/BM25/RRF/fallback/generation nối end-to-end | `src/task7_*` đến `task10_*`, `app.py` | Done |
| Delivery | Rà soát README, dữ liệu, evaluation, reports và secret/cache | `README.md`, `.gitignore`, `reports/` | Done |
| Demo | Chuẩn bị query trong/ngoài domain, PageIndex và kết quả A/B | README và RESULT | Done |

## Quyết định kỹ thuật

- Chọn hybrid + RRF làm cấu hình mặc định dựa trên average A/B cao hơn 0.0219.
- Giữ threshold 0.50 theo sáu query hiệu chỉnh; fallback luôn fail-safe về hybrid nếu provider lỗi.

## Kiểm thử

- Xác nhận đủ 3 legal, 6 news, 9 standardized documents và 665 chunks.
- Kiểm tra PageIndex upload/cache ba PDF và pipeline trả `retrieval_method=pageindex` trong demo.
- Chạy ba checkpoint test trước khi bàn giao.

## Hạn chế

- PageIndex REST retrieval endpoint hiện cảnh báo deprecation; cần chuyển sang API kế nhiệm khi starter/rubric cho phép.
- Cần bảo đảm tất cả nhánh/PR cá nhân tồn tại trên remote trước khi nộp VLearn.

## Xác nhận

Ownership trên được đối chiếu bằng artifact nhóm. Nhánh/commit cá nhân cần được giữ trên remote để giảng viên xác minh lịch sử đóng góp.

- Ngày: 20/09/2026
- Thành viên: Nguyễn Đình Phúc