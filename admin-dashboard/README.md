# Admin Dashboard

Dashboard web nho gon de admin thao tac nhanh voi API backend.

## Tinh nang

- Tai danh sach ma co phieu tu `GET /api/all-symbol`
- Chon ma co phieu va goi `POST /api/price/{symbol}` de cap nhat gia moi nhat
- Goi `POST /api/articles/update` de cap nhat tin tuc
- Tuy chon cap nhat tin tuc theo ma: `POST /api/articles/update?symbol=VNM`
- Hien thi JSON response va lich su thao tac

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
