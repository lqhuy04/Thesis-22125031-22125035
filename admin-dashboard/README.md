# Admin Dashboard

Dashboard web nho gon de admin thao tac nhanh voi API backend.

## Tinh nang

- Tai danh sach ma co phieu tu `GET /api/all-symbol`
- Chon ma co phieu va goi `POST /api/price/{symbol}` de cap nhat gia moi nhat
- Goi `POST /api/articles/update` de cap nhat tin tuc
- Tuy chon cap nhat tin tuc theo ma: `POST /api/articles/update?symbol=VNM`
- Hien thi JSON response va lich su thao tac
- Chay Backtest pipeline (chi admin) va truc quan hoa
- Phan tich AI (chi admin): 1 ma, hoac ca ro VN30 / VN100

## Dang nhap admin (tu dong)

Cac API backtest / phan tich AI yeu cau quyen admin. Dashboard tu dong dang nhap
khi mo bang cach goi `POST /api/auth/admin-login` — backend dung credential trong
`.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`) nen credential khong nam trong frontend.

Yeu cau:

1. Tao 1 tai khoan trong bang `User`, set `role = 'admin'` va `status = 'verified'`.
2. Dat `ADMIN_EMAIL` va `ADMIN_PASSWORD` trong `backend/.env` khop voi tai khoan do.
3. Them origin cua dashboard vao `CORS_ORIGINS` (mac dinh da co `http://localhost:5500`,
   `http://127.0.0.1:5500`).

Trang thai dang nhap hien o goc phai thanh tab. Token het han se tu dong dang nhap lai.

## Chay dashboard

1. Chay backend FastAPI o cong `8000`.
2. Chay static server:

```bash
python -m http.server 5500
```

3. Mo trinh duyet:

- Neu dang o trong folder `admin-dashboard` khi chay lenh:

	- `http://localhost:5500/`
	- `http://localhost:5500/index.html`

- Neu chay lenh tu thu muc goc workspace:

	- `http://localhost:5500/admin-dashboard/`

4. Neu backend khong o `http://localhost:8000`, sua o o `API Base URL` tren giao dien.
