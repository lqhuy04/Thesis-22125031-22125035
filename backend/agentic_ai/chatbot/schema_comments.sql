-- =============================================================================
-- schema_comments.sql — Mô tả ngữ nghĩa (COMMENT ON) cho các bảng chatbot được
-- phép truy vấn (ALLOWED_TABLES trong sql_runner.py).
--
-- Chạy 1 lần trên Supabase Postgres (idempotent — COMMENT ghi đè comment cũ).
-- get_schema_ddl() sẽ đọc các comment này qua pg_catalog và nhét vào prompt của
-- LLM, giúp chatbot hiểu ý nghĩa bảng/cột thay vì chỉ thấy tên + kiểu dữ liệu.
--
-- LƯU Ý: Stock_Price_15m và Stock_Price_1h nằm trong ALLOWED_TABLES nhưng CHƯA
-- tồn tại trong DB hiện tại → không có COMMENT ở đây. Khi nào tạo bảng thật thì
-- bổ sung (áp dụng cùng quy tắc ×1000 như 1d/1m nếu lưu giá đã chia 1000).
-- =============================================================================

-- ─── Stock ───────────────────────────────────────────────────────────────────
COMMENT ON TABLE  public."Stock" IS
  'Danh mục mã cổ phiếu niêm yết; mỗi dòng là một mã CK. Bảng gốc — các bảng khác join qua stock_id = Stock.id.';
COMMENT ON COLUMN public."Stock".id IS 'Khóa chính (uuid), được các bảng khác tham chiếu qua stock_id.';
COMMENT ON COLUMN public."Stock".stock_symbol IS 'Mã cổ phiếu, viết HOA (vd VNM, HPG, FPT).';

-- ─── Current_Stock_Price ──────────────────────────────────────────────────────
COMMENT ON TABLE  public."Current_Stock_Price" IS
  'Giá khớp lệnh MỚI NHẤT (real-time) của từng mã. Đơn vị VNĐ, GIÁ TRỊ THẬT — KHÔNG chia 1000.';
COMMENT ON COLUMN public."Current_Stock_Price".symbol IS 'Mã cổ phiếu (viết hoa).';
COMMENT ON COLUMN public."Current_Stock_Price".price_change IS 'Thay đổi giá so với giá tham chiếu (VNĐ).';
COMMENT ON COLUMN public."Current_Stock_Price".per_price_change IS 'Phần trăm thay đổi giá so với tham chiếu (%).';
COMMENT ON COLUMN public."Current_Stock_Price".ceiling_price IS 'Giá trần trong phiên (VNĐ).';
COMMENT ON COLUMN public."Current_Stock_Price".floor_price IS 'Giá sàn trong phiên (VNĐ).';
COMMENT ON COLUMN public."Current_Stock_Price".ref_price IS 'Giá tham chiếu đầu phiên (VNĐ).';
COMMENT ON COLUMN public."Current_Stock_Price".current_price IS 'Giá khớp hiện tại / gần nhất (VNĐ).';
COMMENT ON COLUMN public."Current_Stock_Price".total_match_vol IS 'Tổng khối lượng khớp lệnh (số cổ phiếu).';
COMMENT ON COLUMN public."Current_Stock_Price".total_match_val IS 'Tổng giá trị khớp lệnh (VNĐ).';

-- ─── Current_Market_Index ─────────────────────────────────────────────────────
COMMENT ON TABLE  public."Current_Market_Index" IS
  'Trạng thái MỚI NHẤT của các chỉ số thị trường (VN-Index, HNX-Index, UPCOM, VN30...). index_value là điểm số — KHÔNG chia 1000.';
COMMENT ON COLUMN public."Current_Market_Index".index_id IS 'Mã chỉ số (vd VNINDEX, HNXINDEX, UPCOM, VN30).';
COMMENT ON COLUMN public."Current_Market_Index".index_name IS 'Tên hiển thị của chỉ số.';
COMMENT ON COLUMN public."Current_Market_Index".type_index IS 'Phân loại chỉ số (main/sector...).';
COMMENT ON COLUMN public."Current_Market_Index".index_value IS 'Giá trị (điểm số) hiện tại của chỉ số.';
COMMENT ON COLUMN public."Current_Market_Index".change IS 'Thay đổi điểm so với phiên trước.';
COMMENT ON COLUMN public."Current_Market_Index".ratio_change IS 'Phần trăm thay đổi của chỉ số (%).';
COMMENT ON COLUMN public."Current_Market_Index".advances IS 'Số mã tăng giá.';
COMMENT ON COLUMN public."Current_Market_Index".no_changes IS 'Số mã đứng giá (tham chiếu).';
COMMENT ON COLUMN public."Current_Market_Index".declines IS 'Số mã giảm giá.';
COMMENT ON COLUMN public."Current_Market_Index".ceilings IS 'Số mã tăng trần.';
COMMENT ON COLUMN public."Current_Market_Index".floors IS 'Số mã giảm sàn.';
COMMENT ON COLUMN public."Current_Market_Index".total_match_vol IS 'Tổng khối lượng khớp lệnh toàn sàn.';
COMMENT ON COLUMN public."Current_Market_Index".total_match_val IS 'Tổng giá trị khớp lệnh toàn sàn (VNĐ).';
COMMENT ON COLUMN public."Current_Market_Index".total_deal_vol IS 'Tổng khối lượng giao dịch thỏa thuận.';
COMMENT ON COLUMN public."Current_Market_Index".total_deal_val IS 'Tổng giá trị giao dịch thỏa thuận (VNĐ).';
COMMENT ON COLUMN public."Current_Market_Index".total_vol IS 'Tổng khối lượng giao dịch (khớp + thỏa thuận).';
COMMENT ON COLUMN public."Current_Market_Index".total_val IS 'Tổng giá trị giao dịch (VNĐ).';
COMMENT ON COLUMN public."Current_Market_Index".trading_date IS 'Ngày giao dịch (chuỗi).';
COMMENT ON COLUMN public."Current_Market_Index".trading_time IS 'Thời điểm cập nhật trong phiên (chuỗi).';
COMMENT ON COLUMN public."Current_Market_Index".trading_session IS 'Phiên giao dịch (mở cửa/khớp lệnh liên tục/đóng cửa...).';

-- ─── MarketIndex / Stock_MarketIndex (danh mục & thành phần chỉ số) ────────────
COMMENT ON TABLE  public."MarketIndex" IS
  'Danh mục các chỉ số thị trường (vd VN-Index, VN30...). Liên kết với "Stock" qua bảng nối "Stock_MarketIndex".';
COMMENT ON COLUMN public."MarketIndex".name IS 'Tên chỉ số.';

COMMENT ON TABLE  public."Stock_MarketIndex" IS
  'Bảng nối nhiều-nhiều giữa "Stock" và "MarketIndex": mỗi dòng gắn 1 mã vào rổ của 1 chỉ số (vd thành phần VN30).';
COMMENT ON COLUMN public."Stock_MarketIndex".stock_id IS 'FK → Stock.id.';
COMMENT ON COLUMN public."Stock_MarketIndex".market_index_id IS 'FK → MarketIndex.id.';

-- ─── Stock_Price_1m (nến 1 phút) ───────────────────────────────────────────────
COMMENT ON TABLE  public."Stock_Price_1m" IS
  'Nến (OHLCV) khung 1 PHÚT theo mã. ⚠ open/high/low/close/volume ĐÃ CHIA 1000 — phải NHÂN 1000 trong SQL để ra giá trị thật.';
COMMENT ON COLUMN public."Stock_Price_1m".symbol IS 'Mã cổ phiếu (viết hoa).';
COMMENT ON COLUMN public."Stock_Price_1m".trading_time IS 'Mốc thời gian của cây nến (timestamptz).';
COMMENT ON COLUMN public."Stock_Price_1m".open IS 'Giá mở cửa — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1m".high IS 'Giá cao nhất — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1m".low IS 'Giá thấp nhất — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1m".close IS 'Giá đóng cửa — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1m".volume IS 'Khối lượng — ĐÃ CHIA 1000, nhân 1000 khi query.';

-- ─── Stock_Price_1d (nến ngày) ─────────────────────────────────────────────────
COMMENT ON TABLE  public."Stock_Price_1d" IS
  'Nến (OHLCV) khung NGÀY theo mã. ⚠ open/high/low/close/volume ĐÃ CHIA 1000 — phải NHÂN 1000 trong SQL để ra giá trị thật. Dùng để tính chỉ báo kỹ thuật (RSI/MACD/KDJ) vì các chỉ báo này KHÔNG lưu trong DB.';
COMMENT ON COLUMN public."Stock_Price_1d".symbol IS 'Mã cổ phiếu (viết hoa).';
COMMENT ON COLUMN public."Stock_Price_1d".trading_time IS 'Ngày giao dịch của cây nến (timestamptz).';
COMMENT ON COLUMN public."Stock_Price_1d".open IS 'Giá mở cửa — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1d".high IS 'Giá cao nhất — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1d".low IS 'Giá thấp nhất — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1d".close IS 'Giá đóng cửa — ĐÃ CHIA 1000, nhân 1000 khi query (VNĐ).';
COMMENT ON COLUMN public."Stock_Price_1d".volume IS 'Khối lượng — ĐÃ CHIA 1000, nhân 1000 khi query.';

-- ─── FA_Summary ────────────────────────────────────────────────────────────────
COMMENT ON TABLE  public."FA_Summary" IS
  'Tóm tắt phân tích cơ bản (dạng văn bản) cho từng mã. Dùng cho câu hỏi định tính "đánh giá/tiềm năng/sức khỏe tài chính".';
COMMENT ON COLUMN public."FA_Summary".summary IS 'Nội dung tóm tắt phân tích cơ bản (text tiếng Việt).';
COMMENT ON COLUMN public."FA_Summary".stock_id IS 'FK → Stock.id.';

-- ─── FA_Indicator (chỉ số tài chính theo năm) ──────────────────────────────────
COMMENT ON TABLE  public."FA_Indicator" IS
  'Chỉ số tài chính theo NĂM (mỗi dòng = 1 mã × 1 năm): định giá, sinh lời, thanh khoản, đòn bẩy, hiệu quả, và các chỉ số riêng ngành ngân hàng.';
COMMENT ON COLUMN public."FA_Indicator".year IS 'Năm tài chính.';
COMMENT ON COLUMN public."FA_Indicator".stock_id IS 'FK → Stock.id.';
COMMENT ON COLUMN public."FA_Indicator".net_income IS 'Lợi nhuận sau thuế (VNĐ).';
COMMENT ON COLUMN public."FA_Indicator".profit_yoy IS 'Tăng trưởng lợi nhuận so với cùng kỳ năm trước.';
COMMENT ON COLUMN public."FA_Indicator".revenue IS 'Doanh thu (VNĐ).';
COMMENT ON COLUMN public."FA_Indicator".revenue_yoy IS 'Tăng trưởng doanh thu so với cùng kỳ năm trước.';
COMMENT ON COLUMN public."FA_Indicator".market_cap IS 'Vốn hóa thị trường (VNĐ).';
COMMENT ON COLUMN public."FA_Indicator".eps IS 'EPS — lãi cơ bản trên mỗi cổ phiếu.';
COMMENT ON COLUMN public."FA_Indicator".pe_ratio IS 'P/E — hệ số giá trên thu nhập.';
COMMENT ON COLUMN public."FA_Indicator".pb_ratio IS 'P/B — hệ số giá trên giá trị sổ sách.';
COMMENT ON COLUMN public."FA_Indicator".ps_ratio IS 'P/S — hệ số giá trên doanh thu.';
COMMENT ON COLUMN public."FA_Indicator".p_cash_flow IS 'P/CF — hệ số giá trên dòng tiền.';
COMMENT ON COLUMN public."FA_Indicator".shares_outstanding IS 'Số cổ phiếu đang lưu hành.';
COMMENT ON COLUMN public."FA_Indicator".ev_ebitda IS 'EV/EBITDA — giá trị doanh nghiệp trên EBITDA.';
COMMENT ON COLUMN public."FA_Indicator".bvps IS 'BVPS — giá trị sổ sách trên mỗi cổ phiếu.';
COMMENT ON COLUMN public."FA_Indicator".cash_ratio IS 'Tỷ số tiền mặt.';
COMMENT ON COLUMN public."FA_Indicator".debt_to_equity IS 'D/E — nợ trên vốn chủ sở hữu.';
COMMENT ON COLUMN public."FA_Indicator".roe IS 'ROE — tỷ suất sinh lời trên vốn chủ sở hữu.';
COMMENT ON COLUMN public."FA_Indicator".roa IS 'ROA — tỷ suất sinh lời trên tổng tài sản.';
COMMENT ON COLUMN public."FA_Indicator".roic IS 'ROIC — tỷ suất sinh lời trên vốn đầu tư.';
COMMENT ON COLUMN public."FA_Indicator".days_receivable IS 'Số ngày phải thu bình quân.';
COMMENT ON COLUMN public."FA_Indicator".days_inventory IS 'Số ngày tồn kho bình quân.';
COMMENT ON COLUMN public."FA_Indicator".days_payable IS 'Số ngày phải trả bình quân.';
COMMENT ON COLUMN public."FA_Indicator".cash_cycle_days IS 'Vòng quay tiền mặt (ngày).';
COMMENT ON COLUMN public."FA_Indicator".quick_ratio IS 'Tỷ số thanh toán nhanh.';
COMMENT ON COLUMN public."FA_Indicator".current_ratio IS 'Tỷ số thanh toán hiện hành.';
COMMENT ON COLUMN public."FA_Indicator".gross_margin IS 'Biên lợi nhuận gộp.';
COMMENT ON COLUMN public."FA_Indicator".ebit_margin IS 'Biên lợi nhuận EBIT.';
COMMENT ON COLUMN public."FA_Indicator".net_margin IS 'Biên lợi nhuận ròng.';
COMMENT ON COLUMN public."FA_Indicator".asset_turnover IS 'Vòng quay tổng tài sản.';
COMMENT ON COLUMN public."FA_Indicator".fixed_asset_turnover IS 'Vòng quay tài sản cố định.';
COMMENT ON COLUMN public."FA_Indicator".loans_to_equity IS 'Nợ vay trên vốn chủ sở hữu.';
COMMENT ON COLUMN public."FA_Indicator".financial_leverage IS 'Đòn bẩy tài chính (tổng tài sản / vốn chủ sở hữu).';
COMMENT ON COLUMN public."FA_Indicator".interest_coverage IS 'Hệ số khả năng thanh toán lãi vay.';
-- Chỉ số riêng ngành ngân hàng (chỉ có giá trị với mã ngân hàng):
COMMENT ON COLUMN public."FA_Indicator".casa_ratio IS '[Ngân hàng] Tỷ lệ tiền gửi không kỳ hạn (CASA).';
COMMENT ON COLUMN public."FA_Indicator".car IS '[Ngân hàng] Tỷ lệ an toàn vốn (CAR).';
COMMENT ON COLUMN public."FA_Indicator".net_interest_income IS '[Ngân hàng] Thu nhập lãi thuần (VNĐ).';
COMMENT ON COLUMN public."FA_Indicator".nii_growth IS '[Ngân hàng] Tăng trưởng thu nhập lãi thuần.';
COMMENT ON COLUMN public."FA_Indicator".credit_growth IS '[Ngân hàng] Tăng trưởng tín dụng.';
COMMENT ON COLUMN public."FA_Indicator".deposit_growth IS '[Ngân hàng] Tăng trưởng huy động tiền gửi.';
COMMENT ON COLUMN public."FA_Indicator".nim IS '[Ngân hàng] Biên lãi ròng (NIM).';
COMMENT ON COLUMN public."FA_Indicator".yield_on_earning_assets IS '[Ngân hàng] Lợi suất trên tài sản sinh lời.';
COMMENT ON COLUMN public."FA_Indicator".cost_of_funds IS '[Ngân hàng] Chi phí vốn.';
COMMENT ON COLUMN public."FA_Indicator".non_interest_to_interest_income IS '[Ngân hàng] Tỷ lệ thu ngoài lãi trên thu từ lãi.';
COMMENT ON COLUMN public."FA_Indicator".cir IS '[Ngân hàng] Tỷ lệ chi phí trên thu nhập (CIR).';
COMMENT ON COLUMN public."FA_Indicator".equity_to_liabilities IS '[Ngân hàng] Vốn chủ sở hữu trên nợ phải trả.';
COMMENT ON COLUMN public."FA_Indicator".equity_to_loans IS '[Ngân hàng] Vốn chủ sở hữu trên dư nợ cho vay.';
COMMENT ON COLUMN public."FA_Indicator".equity_to_assets IS '[Ngân hàng] Vốn chủ sở hữu trên tổng tài sản.';
COMMENT ON COLUMN public."FA_Indicator".ldr IS '[Ngân hàng] Tỷ lệ dư nợ trên tiền gửi (LDR).';
COMMENT ON COLUMN public."FA_Indicator".npl_ratio IS '[Ngân hàng] Tỷ lệ nợ xấu (NPL).';
COMMENT ON COLUMN public."FA_Indicator".npl_coverage_ratio IS '[Ngân hàng] Tỷ lệ bao phủ nợ xấu.';
COMMENT ON COLUMN public."FA_Indicator".loan_loss_reserve_ratio IS '[Ngân hàng] Tỷ lệ dự phòng rủi ro cho vay.';
COMMENT ON COLUMN public."FA_Indicator".provision_expense_to_loans IS '[Ngân hàng] Chi phí dự phòng trên dư nợ cho vay.';

-- ─── FA_BalanceSheet (cân đối kế toán theo năm) ────────────────────────────────
COMMENT ON TABLE  public."FA_BalanceSheet" IS
  'Bảng cân đối kế toán theo NĂM (mỗi dòng = 1 mã × 1 năm). Các giá trị là số tiền (VNĐ).';
COMMENT ON COLUMN public."FA_BalanceSheet".year IS 'Năm tài chính.';
COMMENT ON COLUMN public."FA_BalanceSheet".stock_id IS 'FK → Stock.id.';
COMMENT ON COLUMN public."FA_BalanceSheet".total_assets IS 'Tổng tài sản.';
COMMENT ON COLUMN public."FA_BalanceSheet".current_assets IS 'Tài sản ngắn hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".cash_and_equivalents IS 'Tiền và tương đương tiền.';
COMMENT ON COLUMN public."FA_BalanceSheet".short_term_investments_net IS 'Đầu tư tài chính ngắn hạn (thuần).';
COMMENT ON COLUMN public."FA_BalanceSheet".accounts_receivable IS 'Các khoản phải thu.';
COMMENT ON COLUMN public."FA_BalanceSheet".inventory_net IS 'Hàng tồn kho (thuần).';
COMMENT ON COLUMN public."FA_BalanceSheet".long_term_assets IS 'Tài sản dài hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".fixed_assets IS 'Tài sản cố định.';
COMMENT ON COLUMN public."FA_BalanceSheet".long_term_investments IS 'Đầu tư tài chính dài hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".total_liabilities IS 'Tổng nợ phải trả.';
COMMENT ON COLUMN public."FA_BalanceSheet".current_liabilities IS 'Nợ ngắn hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".accounts_payable IS 'Các khoản phải trả người bán.';
COMMENT ON COLUMN public."FA_BalanceSheet".short_term_loans IS 'Vay và nợ thuê tài chính ngắn hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".long_term_liabilities IS 'Nợ dài hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".long_term_loans IS 'Vay và nợ thuê tài chính dài hạn.';
COMMENT ON COLUMN public."FA_BalanceSheet".equity IS 'Vốn chủ sở hữu.';
COMMENT ON COLUMN public."FA_BalanceSheet".paid_in_capital IS 'Vốn góp của chủ sở hữu (vốn điều lệ đã góp).';
COMMENT ON COLUMN public."FA_BalanceSheet".retained_earnings IS 'Lợi nhuận sau thuế chưa phân phối.';
COMMENT ON COLUMN public."FA_BalanceSheet".total_liabilities_and_equity IS 'Tổng cộng nguồn vốn (nợ + vốn chủ sở hữu).';

-- ─── FA_CashFlow (lưu chuyển tiền tệ theo năm) ─────────────────────────────────
COMMENT ON TABLE  public."FA_CashFlow" IS
  'Báo cáo lưu chuyển tiền tệ theo NĂM (mỗi dòng = 1 mã × 1 năm). Giá trị là số tiền (VNĐ).';
COMMENT ON COLUMN public."FA_CashFlow".year IS 'Năm tài chính.';
COMMENT ON COLUMN public."FA_CashFlow".stock_id IS 'FK → Stock.id.';
COMMENT ON COLUMN public."FA_CashFlow".cfo IS 'Lưu chuyển tiền thuần từ hoạt động kinh doanh.';
COMMENT ON COLUMN public."FA_CashFlow".profit_before_wc_changes IS 'Lợi nhuận trước thay đổi vốn lưu động.';
COMMENT ON COLUMN public."FA_CashFlow".profit_before_tax_cf IS 'Lợi nhuận trước thuế (trên báo cáo LCTT).';
COMMENT ON COLUMN public."FA_CashFlow".depreciation IS 'Khấu hao tài sản cố định.';
COMMENT ON COLUMN public."FA_CashFlow".cfi IS 'Lưu chuyển tiền thuần từ hoạt động đầu tư.';
COMMENT ON COLUMN public."FA_CashFlow".capex IS 'Chi đầu tư tài sản cố định (CapEx).';
COMMENT ON COLUMN public."FA_CashFlow".dividends_received IS 'Cổ tức, lợi nhuận được nhận.';
COMMENT ON COLUMN public."FA_CashFlow".cff IS 'Lưu chuyển tiền thuần từ hoạt động tài chính.';
COMMENT ON COLUMN public."FA_CashFlow".proceeds_from_share_issuance IS 'Tiền thu từ phát hành cổ phiếu.';
COMMENT ON COLUMN public."FA_CashFlow".proceeds_from_loans IS 'Tiền thu từ đi vay.';
COMMENT ON COLUMN public."FA_CashFlow".repayment_of_loans IS 'Tiền trả nợ gốc vay.';
COMMENT ON COLUMN public."FA_CashFlow".dividends_paid IS 'Cổ tức đã trả cho chủ sở hữu.';
COMMENT ON COLUMN public."FA_CashFlow".net_cash_change IS 'Lưu chuyển tiền thuần trong kỳ.';
COMMENT ON COLUMN public."FA_CashFlow".cash_beginning IS 'Tiền và tương đương tiền đầu kỳ.';
COMMENT ON COLUMN public."FA_CashFlow".cash_ending IS 'Tiền và tương đương tiền cuối kỳ.';

-- ─── FA_IncomeStatement (kết quả kinh doanh theo năm) ──────────────────────────
COMMENT ON TABLE  public."FA_IncomeStatement" IS
  'Báo cáo kết quả kinh doanh theo NĂM (mỗi dòng = 1 mã × 1 năm). Giá trị là số tiền (VNĐ), trừ eps_basic.';
COMMENT ON COLUMN public."FA_IncomeStatement".year IS 'Năm tài chính.';
COMMENT ON COLUMN public."FA_IncomeStatement".stock_id IS 'FK → Stock.id.';
COMMENT ON COLUMN public."FA_IncomeStatement".gross_revenue IS 'Doanh thu bán hàng và cung cấp dịch vụ (gộp).';
COMMENT ON COLUMN public."FA_IncomeStatement".net_revenue IS 'Doanh thu thuần.';
COMMENT ON COLUMN public."FA_IncomeStatement".cogs IS 'Giá vốn hàng bán.';
COMMENT ON COLUMN public."FA_IncomeStatement".gross_profit IS 'Lợi nhuận gộp.';
COMMENT ON COLUMN public."FA_IncomeStatement".financial_income IS 'Doanh thu hoạt động tài chính.';
COMMENT ON COLUMN public."FA_IncomeStatement".financial_expense IS 'Chi phí tài chính.';
COMMENT ON COLUMN public."FA_IncomeStatement".interest_expense IS 'Chi phí lãi vay.';
COMMENT ON COLUMN public."FA_IncomeStatement".selling_expense IS 'Chi phí bán hàng.';
COMMENT ON COLUMN public."FA_IncomeStatement".admin_expense IS 'Chi phí quản lý doanh nghiệp.';
COMMENT ON COLUMN public."FA_IncomeStatement".operating_profit IS 'Lợi nhuận thuần từ hoạt động kinh doanh.';
COMMENT ON COLUMN public."FA_IncomeStatement".profit_before_tax IS 'Lợi nhuận trước thuế.';
COMMENT ON COLUMN public."FA_IncomeStatement".income_tax_expense IS 'Chi phí thuế thu nhập doanh nghiệp.';
COMMENT ON COLUMN public."FA_IncomeStatement".net_profit_after_tax IS 'Lợi nhuận sau thuế.';
COMMENT ON COLUMN public."FA_IncomeStatement".net_income_parent IS 'Lợi nhuận sau thuế của cổ đông công ty mẹ.';
COMMENT ON COLUMN public."FA_IncomeStatement".eps_basic IS 'EPS cơ bản (lãi trên mỗi cổ phiếu).';
COMMENT ON COLUMN public."FA_IncomeStatement".ebit IS 'Lợi nhuận trước lãi vay và thuế (EBIT).';
COMMENT ON COLUMN public."FA_IncomeStatement".ebitda IS 'Lợi nhuận trước lãi vay, thuế và khấu hao (EBITDA).';

-- ─── FA_Industry_Aggregate (trung vị ngành, precompute) ────────────────────────
COMMENT ON TABLE  public."FA_Industry_Aggregate" IS
  'Chỉ tiêu TRUNG VỊ ngành đã precompute theo (category_id, year) — dùng để so sánh một mã CP với mặt bằng chung của ngành (Category) và tính CAGR ngành. Mỗi dòng = 1 ngành × 1 năm.';
COMMENT ON COLUMN public."FA_Industry_Aggregate".category_id IS 'FK → Category.id (mã ngành).';
COMMENT ON COLUMN public."FA_Industry_Aggregate".year IS 'Năm tài chính.';
COMMENT ON COLUMN public."FA_Industry_Aggregate".peer_count IS 'Số mã CK trong ngành dùng để tính trung vị.';

-- ─── Article (tin tức) ──────────────────────────────────────────────────────────
COMMENT ON TABLE  public."Article" IS
  'Tin tức / bài báo. Liên kết với mã CK qua bảng nối "Article_Stock" (Article.id = Article_Stock.article_id).';
COMMENT ON COLUMN public."Article".title IS 'Tiêu đề bài báo.';
COMMENT ON COLUMN public."Article".link IS 'URL gốc của bài báo (duy nhất).';
COMMENT ON COLUMN public."Article".description IS 'Mô tả ngắn / sapo.';
COMMENT ON COLUMN public."Article".time IS 'Ngày đăng bài (date).';
COMMENT ON COLUMN public."Article".content IS 'Nội dung đầy đủ bài báo.';
COMMENT ON COLUMN public."Article".source IS 'Nguồn báo (vd CafeF, Vietstock).';
COMMENT ON COLUMN public."Article".sentiment IS 'Cảm xúc tin: positive / negative / neutral.';
COMMENT ON COLUMN public."Article".summary IS 'Tóm tắt bài báo (do AI sinh).';
COMMENT ON COLUMN public."Article".thumbnail IS 'URL ảnh đại diện.';
COMMENT ON COLUMN public."Article".article_type IS 'Loại bài: stock (theo mã) / market (thị trường chung)...';

-- ─── Article_Stock (bảng nối tin tức ↔ mã) ─────────────────────────────────────
COMMENT ON TABLE  public."Article_Stock" IS
  'Bảng nối nhiều-nhiều giữa "Article" và "Stock": mỗi dòng gắn 1 bài báo với 1 mã CK.';
COMMENT ON COLUMN public."Article_Stock".article_id IS 'FK → Article.id.';
COMMENT ON COLUMN public."Article_Stock".stock_id IS 'FK → Stock.id.';

-- ─── Article_Category (bảng nối tin tức ↔ ngành) ───────────────────────────────
COMMENT ON TABLE  public."Article_Category" IS
  'Bảng nối nhiều-nhiều giữa "Article" và "Category": mỗi dòng gắn 1 bài báo với 1 ngành (dùng cho tin tức ở cấp ngành thay vì 1 mã cụ thể).';
COMMENT ON COLUMN public."Article_Category".article_id IS 'FK → Article.id.';
COMMENT ON COLUMN public."Article_Category".category_id IS 'FK → Category.id.';

-- ─── Category (danh mục ngành/nhóm) ────────────────────────────────────────────
COMMENT ON TABLE  public."Category" IS
  'Danh mục ngành/nhóm (ICB cấp Industry). Bảng gốc cho câu hỏi liên quan đến NGÀNH — liên kết với "Stock" qua bảng nối "Category_Stock" (Category.id = Category_Stock.category_id).';
COMMENT ON COLUMN public."Category".id IS 'Mã ngành ICB (vd "8300" = Ngân hàng), khóa chính, được "Category_Stock" tham chiếu qua category_id.';
COMMENT ON COLUMN public."Category".category_name IS 'Tên ngành (tiếng Việt), vd "Ngân hàng", "Bất động sản".';

-- ─── Category_Stock (bảng nối mã ↔ ngành) ──────────────────────────────────────
COMMENT ON TABLE  public."Category_Stock" IS
  'Bảng nối nhiều-nhiều giữa "Stock" và ngành/nhóm (Category): mỗi dòng gắn 1 mã với 1 category.';
COMMENT ON COLUMN public."Category_Stock".stock_id IS 'FK → Stock.id.';
COMMENT ON COLUMN public."Category_Stock".category_id IS 'FK → Category.id (mã ngành/nhóm).';

-- ─── BI_Profile (hồ sơ doanh nghiệp) ───────────────────────────────────────────
COMMENT ON TABLE  public."BI_Profile" IS
  'Hồ sơ doanh nghiệp (thông tin niêm yết, quy mô, ngành) cho từng mã. Liên kết Stock qua stock_id; ngoài ra có cột symbol.';
COMMENT ON COLUMN public."BI_Profile".symbol IS 'Mã cổ phiếu (viết hoa, duy nhất).';
COMMENT ON COLUMN public."BI_Profile".company_name IS 'Tên công ty.';
COMMENT ON COLUMN public."BI_Profile".description IS 'Giới thiệu / mô tả hoạt động kinh doanh.';
COMMENT ON COLUMN public."BI_Profile".address IS 'Địa chỉ trụ sở.';
COMMENT ON COLUMN public."BI_Profile".industry_name IS 'Tên ngành.';
COMMENT ON COLUMN public."BI_Profile".icb_code IS 'Mã ngành ICB.';
COMMENT ON COLUMN public."BI_Profile".sic_code IS 'Mã ngành SIC.';
COMMENT ON COLUMN public."BI_Profile".founded_date IS 'Ngày thành lập.';
COMMENT ON COLUMN public."BI_Profile".charter_capital_billion IS 'Vốn điều lệ (tỷ VNĐ).';
COMMENT ON COLUMN public."BI_Profile".employee_count IS 'Số lượng nhân viên.';
COMMENT ON COLUMN public."BI_Profile".branch_count IS 'Số chi nhánh.';
COMMENT ON COLUMN public."BI_Profile".listing_date IS 'Ngày niêm yết.';
COMMENT ON COLUMN public."BI_Profile".exchange IS 'Sàn niêm yết (HOSE/HNX/UPCOM).';
COMMENT ON COLUMN public."BI_Profile".ipo_price IS 'Giá IPO (VNĐ).';
COMMENT ON COLUMN public."BI_Profile".listed_volume IS 'Khối lượng cổ phiếu niêm yết.';
COMMENT ON COLUMN public."BI_Profile".market_cap_billion IS 'Vốn hóa thị trường (tỷ VNĐ).';
COMMENT ON COLUMN public."BI_Profile".shares_outstanding IS 'Số cổ phiếu đang lưu hành.';
COMMENT ON COLUMN public."BI_Profile".stock_id IS 'FK → Stock.id.';

-- ─── BI_Leader (ban lãnh đạo) ──────────────────────────────────────────────────
COMMENT ON TABLE  public."BI_Leader" IS
  'Ban lãnh đạo doanh nghiệp: mỗi dòng là một lãnh đạo của một mã (join qua stock_id).';
COMMENT ON COLUMN public."BI_Leader".full_name IS 'Họ tên lãnh đạo.';
COMMENT ON COLUMN public."BI_Leader".position IS 'Chức vụ (Chủ tịch HĐQT, Tổng giám đốc...).';
COMMENT ON COLUMN public."BI_Leader".stock_id IS 'FK → Stock.id.';

-- ─── BI_Subsidiary (công ty con / liên kết) ────────────────────────────────────
COMMENT ON TABLE  public."BI_Subsidiary" IS
  'Công ty con / công ty liên kết của doanh nghiệp (join qua stock_id).';
COMMENT ON COLUMN public."BI_Subsidiary".company_name IS 'Tên công ty con / liên kết.';
COMMENT ON COLUMN public."BI_Subsidiary".sub_symbol IS 'Mã CK của công ty con (nếu có niêm yết).';
COMMENT ON COLUMN public."BI_Subsidiary".charter_capital_billion IS 'Vốn điều lệ của công ty con (tỷ VNĐ).';
COMMENT ON COLUMN public."BI_Subsidiary".ownership_pct IS 'Tỷ lệ sở hữu của công ty mẹ (%).';
COMMENT ON COLUMN public."BI_Subsidiary".relationship_type IS 'Loại quan hệ: subsidiary (công ty con) / associate (liên kết).';
COMMENT ON COLUMN public."BI_Subsidiary".stock_id IS 'FK → Stock.id (công ty mẹ).';
