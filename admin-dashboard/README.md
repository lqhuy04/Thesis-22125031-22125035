# Stockrium Lab

Công cụ web để người dùng Stockrium thử nghiệm phân tích AI,
backtest và so sánh kết quả.

## Tính năng

- Chạy backtest pipeline cho một mã hoặc rổ VN30 lấy động từ backend.
- Phân tích AI cho một mã, VN30 hoặc VN100.
- Xem kết quả JSON, lịch sử backtest và biểu đồ.
- Tự lưu checkpoint sau từng mã VN30; chạy lại cùng cấu hình sẽ bỏ qua mã đã
  thành công và retry các mã lỗi. Không có token hoặc mật khẩu nào được lưu
  trong checkpoint; checkpoint được tách riêng theo user.
- Lịch sử và file kết quả backtest chỉ hiển thị cho user sở hữu.
- Mỗi lần chạy backtest hoặc phân tích AI tạo một Experiment có trạng thái
  `running`, `completed` hoặc `failed`; tab **Lịch sử thử nghiệm** cho phép lọc
  theo loại/trạng thái và xem lại cấu hình, kết quả của tài khoản hiện tại.
- Chọn từ 2 đến 5 Experiment để so sánh song song cấu hình nguồn dữ liệu,
  trọng số, tham số chạy và các chỉ số kết quả. Những chỉ số tốt nhất được đánh
  dấu trực quan; có thể đối chiếu cả backtest và phân tích AI.
- Experiment mới lưu metadata tái lập: hash cấu hình chuẩn hóa, fingerprint lần
  chạy, phiên bản ứng dụng/code/pipeline/prompt/model và trạng thái snapshot dữ
  liệu. Có thể sao chép **gói tái lập** từ màn chi tiết.
- Metadata ghi rõ mức `configuration_only`: cấu hình được giữ nguyên nhưng dữ
  liệu live và đầu ra LLM chưa thể tái lập tuyệt đối khi chưa có snapshot bất biến
  và model seed.
- Cảnh báo “Không phải khuyến nghị đầu tư” luôn xuất hiện trên web và được trả
  kèm kết quả API phân tích/backtest.

## Đăng nhập

Stockrium Lab hiển thị form email/mật khẩu, gửi thông tin tới
`POST /api/auth/login`, rồi xác minh phiên qua `GET /api/auth/me`.
Access token và refresh token chỉ được giữ trong bộ nhớ của trang.
Khi Stockrium Lab còn mở, access token được tự động gia hạn trước khi hết hạn;
request gặp `401` sẽ refresh và retry một lần. Refresh token được xoay vòng
sau mỗi lần gia hạn, nên phiên đang hoạt động không bị dừng giữa batch
VN30.

Stockrium Lab sử dụng các API thử nghiệm:

- `POST /api/agentic/experiments/analyze`
- `GET /api/agentic/experiments`
- `GET /api/agentic/experiments/{experiment_id}`
- `POST /api/agentic/experiments/compare`
- `GET /api/agentic/market-universes/{name}`

Các endpoint `/admin-analyze` và `/admin-universe/{name}` cũ được giữ làm
alias tương thích trong giai đoạn chuyển đổi.

Yêu cầu:

1. Tạo tài khoản trong bảng `User` và đảm bảo tài khoản có
   `status = 'verified'`.
2. Thêm origin của Stockrium Lab vào `CORS_ORIGINS`, ví dụ
   `http://localhost:5500` và `http://127.0.0.1:5500`.

Không đặt mật khẩu, API key hoặc giá trị `.env` trong file frontend.
Stockrium Lab chỉ yêu cầu đăng nhập lại khi không thể gia hạn hoặc khi người dùng chủ
động đăng xuất.

Khi deploy backend, đặt `CODE_REVISION` bằng Git commit SHA. Railway có thể dùng
`RAILWAY_GIT_COMMIT_SHA` làm giá trị dự phòng. Nếu bỏ trống, Experiment sẽ ghi
`code_revision = "unknown"` và không thể xác nhận chính xác phiên bản code.

## Chạy Stockrium Lab

1. Chạy backend FastAPI ở cổng `8000`.
2. Trong thư mục `admin-dashboard`, chạy:

```bash
python -m http.server 5500
```

3. Mở `http://localhost:5500/`.
4. URL backend không hiển thị cho người dùng. Khi chạy local hoặc đổi môi trường
   deploy, cấu hình `API_BASE_URL` trong `config.js`; ví dụ
   `http://localhost:8000` cho backend local.
