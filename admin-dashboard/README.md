# Admin Dashboard

Dashboard web nhỏ gọn để quản trị viên thao tác với API backend.

## Tính năng

- Tải danh sách mã cổ phiếu từ `GET /api/all-symbol`.
- Cập nhật giá và tin tức.
- Chạy backtest pipeline và phân tích AI dành riêng cho admin.
- Xem kết quả JSON, lịch sử thao tác và biểu đồ.

## Đăng nhập admin

Dashboard hiển thị form email/mật khẩu, gửi thông tin tới
`POST /api/auth/login`, rồi xác minh quyền qua `GET /api/auth/admin-session`.
Access token và refresh token chỉ được giữ trong bộ nhớ của trang.

Yêu cầu:

1. Tạo tài khoản trong bảng `User`, đặt `role = 'admin'` và
   `status = 'verified'`.
2. Thêm origin của dashboard vào `CORS_ORIGINS`, ví dụ
   `http://localhost:5500` và `http://127.0.0.1:5500`.

Không đặt mật khẩu admin, API key hoặc giá trị `.env` trong file frontend.
Khi token hết hạn, dashboard sẽ yêu cầu đăng nhập lại.

## Chạy dashboard

1. Chạy backend FastAPI ở cổng `8000`.
2. Trong thư mục `admin-dashboard`, chạy:

```bash
python -m http.server 5500
```

3. Mở `http://localhost:5500/`.
4. Nếu backend không ở `http://localhost:8000`, sửa ô `API Base URL`.
