-- Bảng tổng hợp chỉ tiêu TRUNG VỊ theo ngành ICB cấp Industry, theo từng năm.
-- Precompute bằng utils/precompute_industry_aggregate/precompute_industry_aggregate.py
-- rồi đọc trong luồng /analyze để so sánh mã cổ phiếu với mặt bằng ngành + CAGR.
--
-- category_id: mã ngành ICB cấp Industry như bảng `category` lưu (0001, 1000, ...,
-- 9000). Gộp theo nguyên lý chữ số đầu của mã ICB chi tiết: '0'→'0001', 'd'→'d000'.
CREATE TABLE IF NOT EXISTS "FA_Industry_Aggregate" (
    category_id TEXT NOT NULL,
    year        INT  NOT NULL,
    peer_count  INT,                 -- số mã có dữ liệu trong năm (độ tin cậy trung vị)

    -- Trung vị các chỉ tiêu (đầy đủ để dùng lại; /analyze chỉ đọc một phần chọn lọc).
    roe                  FLOAT,
    roa                  FLOAT,
    roic                 FLOAT,
    gross_margin         FLOAT,
    ebit_margin          FLOAT,
    net_margin           FLOAT,
    asset_turnover       FLOAT,
    fixed_asset_turnover FLOAT,
    debt_to_equity       FLOAT,
    financial_leverage   FLOAT,
    loans_to_equity      FLOAT,
    interest_coverage    FLOAT,
    current_ratio        FLOAT,
    quick_ratio          FLOAT,
    cash_ratio           FLOAT,
    days_inventory       FLOAT,
    days_receivable      FLOAT,
    pe_ratio             FLOAT,
    pb_ratio             FLOAT,
    ps_ratio             FLOAT,
    ev_ebitda            FLOAT,
    eps                  FLOAT,
    bvps                 FLOAT,

    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (category_id, year)
);

CREATE INDEX IF NOT EXISTS idx_fa_industry_agg_category
    ON "FA_Industry_Aggregate"(category_id);
