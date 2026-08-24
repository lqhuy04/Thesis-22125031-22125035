# Admin Dashboard

Dashboard web nhỏ gọn để người dùng đã xác thực thao tác với API backend.

## Tính năng

- Chạy backtest pipeline cho một mã hoặc rổ VN30 lấy động từ backend.
- Phân tích AI cho một mã, VN30 hoặc VN100.
- Xem kết quả JSON, lịch sử backtest và biểu đồ.
- Tự lưu checkpoint sau từng mã VN30; chạy lại cùng cấu hình sẽ bỏ qua mã đã
  thành công và retry các mã lỗi. Không có token hoặc mật khẩu nào được lưu
  trong checkpoint.

## Đăng nhập

Dashboard hiển thị form email/mật khẩu, gửi thông tin tới
`POST /api/auth/login`, rồi xác minh phiên qua `GET /api/auth/me`.
Access token và refresh token chỉ được giữ trong bộ nhớ của trang.
Khi dashboard còn mở, access token được tự động gia hạn trước khi hết hạn;
request gặp `401` sẽ refresh và retry một lần. Refresh token được xoay vòng
sau mỗi lần gia hạn, nên phiên đang hoạt động không bị dừng giữa batch
VN30.

Yêu cầu:

1. Tạo tài khoản trong bảng `User` và đảm bảo tài khoản có
   `status = 'verified'`.
2. Thêm origin của dashboard vào `CORS_ORIGINS`, ví dụ
   `http://localhost:5500` và `http://127.0.0.1:5500`.

Không đặt mật khẩu, API key hoặc giá trị `.env` trong file frontend.
Dashboard chỉ yêu cầu đăng nhập lại khi không thể gia hạn hoặc khi người dùng chủ
động đăng xuất.

## Chạy dashboard

1. Chạy backend FastAPI ở cổng `8000`.
2. Trong thư mục `admin-dashboard`, chạy:

```bash
python -m http.server 5500
```

3. Mở `http://localhost:5500/`.
4. Nếu backend không ở `http://localhost:8000`, sửa ô `API Base URL`.
