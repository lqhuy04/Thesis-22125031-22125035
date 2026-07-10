"""
SSI iBoard Financial Report Downloader
=======================================
Downloads Excel/CSV files from SSI iBoard fundamental-analysis page
for a given stock symbol by clicking the "TẢI XUỐNG" button on each tab.

Tabs handled
────────────
Tab "Báo cáo tài chính" (Financial Reports)
  └─ Sub-tab "Cân đối kế toán"     → <SYMBOL>_balance_sheet.xlsx
  └─ Sub-tab "Kết quả kinh doanh"  → <SYMBOL>_income_statement.xlsx
  └─ Sub-tab "Lưu chuyển tiền tệ"  → <SYMBOL>_cash_flow.xlsx
Tab "Chỉ số tài chính"             → <SYMBOL>_financial_indicators.xlsx

Usage
─────
  python ssi_financial_downloader.py VNM
  python ssi_financial_downloader.py VNM --output ./downloads --headless
"""

import argparse
import glob
import os
import re
import sys
import time
from typing import Optional

import pandas as pd

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

LOGIN_URL = "https://iboard.ssi.com.vn/auth/login"
BASE_URL  = "https://iboard.ssi.com.vn/analysis/fundamental-analysis"

# How long (s) to wait for a new file to appear after clicking download
DOWNLOAD_WAIT_SEC = 30

# ── Default stock symbol (used when --symbol is passed or for --process-only)
SYMBOL = "VNM"

# Progress file lives next to this script
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_progress.txt")


def _load_all_symbols() -> list:
    """
    Read all_symbols_raw.txt from the crawl_company_profile directory and
    return a filtered list of stock symbols, excluding bond/derivative
    instruments (symbols ending in 4+ digits, e.g. CACB2502).
    """
    symbols_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "crawl_company_profile", "all_symbols_raw.txt",
    )
    symbols_file = os.path.normpath(symbols_file)
    content = ""
    try:
        with open(symbols_file, encoding="utf-8-sig", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Symbol list not found: {symbols_file}")

    # Retry with utf-16 if the content looks corrupt
    if not content or content.startswith("\x00") or "\ufffd" in content[:20]:
        with open(symbols_file, encoding="utf-16") as f:
            content = f.read()

    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find symbol list in all_symbols_raw.txt")

    raw_list: list = eval(match.group())  # safe: known file format
    return [s for s in raw_list if not re.search(r'\d{4,}$', s)]


def _load_progress() -> set:
    """Return the set of symbols already successfully downloaded."""
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE, encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip()}


def _mark_done(symbol: str) -> None:
    """Append a symbol to the progress file."""
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(symbol.upper() + "\n")


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _latest_file_in(directory: str) -> Optional[str]:
    """Return the most-recently-modified file in *directory*, or None."""
    files = glob.glob(os.path.join(directory, "*"))
    files = [f for f in files if os.path.isfile(f)]
    return max(files, key=os.path.getmtime) if files else None


# Map dest filename keywords → substrings to match against "Data Title" rows
_TITLE_KEYWORDS: dict[str, list[str]] = {
    "balance_sheet":         ["balance"],
    "income_statement":      ["income", "profit", "loss", "result"],
    "cash_flow":             ["cash"],
    "financial_indicators":  ["indicator", "ratio", "metric", "financial"],
    "dividends_forecast":    ["dividend", "forecast"],
}


def _clean_sheet(raw: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Given a sheet read with header=None, find the real header row
    (the one whose non-null values include year numbers like 2011-2030),
    re-index from that row, and strip empty / metadata / footer rows.
    Returns None if no data header is found.
    """
    header_row_idx = None
    for i, row in raw.iterrows():
        vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if any(re.match(r'^20[12]\d(\.0)?$', v) for v in vals):
            header_row_idx = i
            break

    if header_row_idx is None:
        return None

    # Use that row as column names
    new_cols = [
        str(raw.iloc[header_row_idx, c]).strip() if pd.notna(raw.iloc[header_row_idx, c]) else f"Col_{c}"
        for c in range(raw.shape[1])
    ]
    df = raw.iloc[header_row_idx + 1:].copy()
    df.columns = new_cols

    # Drop fully-empty rows
    df = df.dropna(how="all")

    # Drop rows with no value in the first (label) column
    df = df[df.iloc[:, 0].notna()]

    # Drop footer / metadata rows
    footer_pat = re.compile(r'Dữ liệu|fiintrade|http|Data Title|Date Of Extract', re.IGNORECASE)
    mask = df.iloc[:, 0].astype(str).apply(lambda x: bool(footer_pat.search(x)))
    df = df[~mask]

    # Drop trailing columns that are all-NaN (extra empty cols)
    df = df.dropna(axis=1, how="all")

    # Fix year columns: strip ".0" suffix from integer-looking column names
    df.columns = [
        re.sub(r'^(\d{4})\.0$', r'\1', c) for c in df.columns
    ]

    df = df.reset_index(drop=True)
    return df if not df.empty else None


def _xlsx_to_csv(src: str, dest: str) -> None:
    """
    Convert an Excel workbook to a clean CSV saved at *dest*.

    Strategy:
      1. Read every sheet with header=None.
      2. Detect the real data header row per sheet (the one with year columns).
      3. Clean metadata rows, empty rows, and footer rows.
      4. If the workbook has only one usable sheet → save it to *dest*.
      5. If the workbook has multiple usable sheets:
           - Try to pick the sheet whose "Data Title" cell best matches
             the keyword implied by *dest* filename.
           - Save that sheet to *dest*; save others alongside with their
             own names derived from the title.
    """
    dest_dir = os.path.dirname(dest)
    dest_base = os.path.basename(dest)          # e.g. VNM_balance_sheet.csv
    dest_stem = dest_base.rsplit(".", 1)[0]     # e.g. VNM_balance_sheet

    # Determine keyword from dest filename for sheet matching
    dest_keyword = None
    for kw in _TITLE_KEYWORDS:
        if kw in dest_stem:
            dest_keyword = kw
            break

    raw_sheets: dict[str, pd.DataFrame] = pd.read_excel(
        src, sheet_name=None, header=None, engine="openpyxl"
    )

    cleaned: list[tuple[str, pd.DataFrame]] = []  # (data_title, df)
    for sheet_name, raw in raw_sheets.items():
        df = _clean_sheet(raw)
        if df is None:
            continue
        # Try to extract the "Data Title" from the raw sheet metadata rows
        data_title = sheet_name  # fallback
        for i, row in raw.iterrows():
            if i >= 10:
                break
            for v in row:
                if isinstance(v, str) and "Data Title" in v:
                    # Next non-null on same row or next row
                    vals = [str(x).strip() for x in row if pd.notna(x) and str(x).strip() not in ("", "Data Title")]
                    if vals:
                        data_title = vals[0]
                    break
        cleaned.append((data_title.lower(), df))

    if not cleaned:
        # Last-resort: naive read
        fallback = pd.read_excel(src, sheet_name=0, engine="openpyxl")
        fallback.to_csv(dest, index=False, encoding="utf-8-sig")
        return

    if len(cleaned) == 1:
        cleaned[0][1].to_csv(dest, index=False, encoding="utf-8-sig")
        return

    # Multiple usable sheets — pick the best match for dest
    best_df = None
    best_title = None
    if dest_keyword:
        keywords_for_key = _TITLE_KEYWORDS[dest_keyword]
        for title, df in cleaned:
            if any(kw in title for kw in keywords_for_key):
                best_df = df
                best_title = title
                break

    if best_df is None:
        # No keyword match — use first sheet
        best_title, best_df = cleaned[0]

    best_df.to_csv(dest, index=False, encoding="utf-8-sig")

    # Save remaining sheets as sibling files
    # Derive symbol prefix from dest_stem  (everything before first "_")
    prefix = dest_stem.split("_")[0]  # e.g. "VNM"
    for title, df in cleaned:
        if df is best_df:
            continue
        # Slug the title into a filename
        slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
        sibling = os.path.join(dest_dir, f"{prefix}_{slug}.csv")
        df.to_csv(sibling, index=False, encoding="utf-8-sig")
        print(f"  Also saved sibling sheet: {os.path.basename(sibling)}")


# Mapping from DB column name → possible Vietnamese indicator labels in the CSV.
#
# Different SSI iBoard indicator templates use different wording for the same
# concept (e.g. banks say "Số cổ phiếu lưu hành", everyone else says "Số CP lưu
# hành"), and banks get a handful of credit-institution-only metrics (CAR, NIM,
# LDR, NPL, CASA, CIR...) that never appear for other symbols. Rather than
# maintaining a separate map per industry template, each column lists every
# label variant we've observed; lookup tries them in order and NULLs out when
# none match (e.g. bank-only columns stay NULL for non-bank symbols).
_INDICATOR_COLUMNS: dict[str, list[str]] = {
    "cash_cycle_days":       ["Chu kỳ tiền"],
    "net_income":            ["Lợi nhuận sau thuế của Cổ đông công ty mẹ"],
    "profit_yoy":            ["Tăng trưởng lợi nhuận (%)", "Tăng trưởng lợi nhuận sau thuế (%)"],
    "revenue":               ["Doanh thu"],
    "revenue_yoy":           ["Tăng trưởng doanh thu (%)"],
    "market_cap":            ["Vốn hóa"],
    "eps":                   ["EPS (VND)"],
    "pe_ratio":              ["P/E"],
    "pb_ratio":              ["P/B"],
    "ps_ratio":              ["P/S"],
    "p_cash_flow":           ["P/Cash Flow"],
    "shares_outstanding":    ["Số CP lưu hành", "Số cổ phiếu lưu hành"],
    "ev_ebitda":             ["EV/EBITDA"],
    "bvps":                  ["BVPS (VND)"],
    "cash_ratio":            ["Chỉ số thanh toán tiền mặt"],
    "debt_to_equity":        ["Nợ/VCSH"],
    "roe":                   ["ROE (%)"],
    "roa":                   ["ROA (%)"],
    "days_receivable":       ["Số ngày thu tiền bình quân"],
    "days_inventory":        ["Số ngày tồn kho bình quân"],
    "quick_ratio":           ["Chỉ số thanh toán nhanh"],
    "days_payable":          ["Số ngày thanh toán bình quân"],
    "gross_margin":          ["Biên lợi nhuận gộp (%)"],
    "ebit_margin":           ["Biên EBIT (%)"],
    "net_margin":            ["Biên lợi nhuận ròng (%)"],
    "current_ratio":         ["Chỉ số thanh toán hiện thời"],
    "asset_turnover":        ["Quay vòng tài sản"],
    "loans_to_equity":       ["(Vay NH + DH)/VCSH"],
    "financial_leverage":    ["Đòn bẩy tài chính"],
    "roic":                  ["ROIC (%)"],
    "interest_coverage":     ["Khả năng chi trả lãi vay"],
    "fixed_asset_turnover":  ["Vòng quay TSCĐ"],

    # ── Bank-only (credit institution) indicators — SSI iBoard only emits
    # these for banks; the column stays NULL for every other symbol.
    "casa_ratio":                     ["Tỉ lệ CASA"],
    "car":                            ["CAR (%)"],
    "net_interest_income":            ["Thu nhập lãi thuần"],
    "nii_growth":                     ["Tăng trưởng thu nhập lãi thuần (%)"],
    "credit_growth":                  ["Tăng trưởng tín dụng (%)"],
    "deposit_growth":                 ["Tăng trưởng tiền gửi (%)"],
    "nim":                            ["NIM (%)"],
    "yield_on_earning_assets":        ["Tỉ suất sinh lời của Tài sản có sinh lãi (YOEA) (%)"],
    "cost_of_funds":                  ["Chi phí tài chính trung bình (COF) (%)"],
    "non_interest_to_interest_income": ["Thu nhập ngoài lãi/ Thu nhập từ lãi (%)"],
    "cir":                            ["Chi phí/ Thu nhập (%)"],
    "equity_to_liabilities":          ["Vốn CSH/ Tổng nợ"],
    "equity_to_loans":                ["Vốn CSH/ Tổng cho vay"],
    "equity_to_assets":               ["Vốn CSH/ Tài sản"],
    "ldr":                            ["LDR (%)"],
    "npl_ratio":                      ["Tỉ lệ nợ xấu (%)"],
    "npl_coverage_ratio":             ["Dự phòng tín RR dụng/ Nợ xấu (%)"],
    "loan_loss_reserve_ratio":        ["Dự phòng RR tín dụng/ Cho vay (%)"],
    "provision_expense_to_loans":     ["Trích lập dự phòng/ Cho vay (%)"],
}


def process_financial_indicators_csv(
    csv_path: str,
    symbol: Optional[str] = None,
) -> pd.DataFrame:
    """
    Parse a *_financial_indicators.csv downloaded from SSI iBoard and return
    a tidy, wide-format DataFrame with one row per (symbol, year).

    CSV layout
    ──────────
    The file uses a paired-row convention for categorised indicators:

        Row A  →  indicator name in col-0, all year values empty
        Row B  →  symbol (e.g. "VNM") in col-0, actual year values

    Some indicators (e.g. growth rates) appear as a single row whose col-0
    is the indicator name *and* col-1..N hold numeric values directly.

    Parameters
    ──────────
    csv_path : str
        Absolute or relative path to the CSV file.
    symbol   : str | None
        Override the symbol used in the output.  When None the symbol is
        inferred from the data rows (the value in the first column of a
        data row, e.g. "VNM").

    Returns
    ───────
    pd.DataFrame
        Columns: symbol, year, <one column per indicator in _INDICATOR_COLUMNS>
        Rows:    one per year (NaN where data was absent).
    """
    raw = pd.read_csv(csv_path, header=0, dtype=str)

    # ── 1. Identify year columns ──────────────────────────────────────────
    year_cols = [c for c in raw.columns if re.match(r'^20[12]\d$', str(c).strip())]
    if not year_cols:
        raise ValueError(f"No year columns found in {csv_path}")

    label_col = raw.columns[0]  # "Chỉ số"

    # ── 2. Walk rows and collect (indicator_name → {year: value}) ─────────
    indicator_data: dict[str, dict[str, Optional[float]]] = {}
    inferred_symbol: Optional[str] = None
    pending_indicator: Optional[str] = None  # name of the category row we just saw

    for _, row in raw.iterrows():
        label = str(row[label_col]).strip() if pd.notna(row[label_col]) else ""

        year_vals = {y: row[y] for y in year_cols}
        has_data = any(
            pd.notna(v) and str(v).strip() not in ("", "nan")
            for v in year_vals.values()
        )

        if not has_data:
            # Category / header row  →  remember as the pending indicator
            if label:
                pending_indicator = label
        else:
            # A row with actual numeric values
            # Is this a symbol data row (e.g. "VNM") or a standalone metric row?
            is_symbol_row = bool(re.match(r'^[A-Z]{2,10}$', label))

            if is_symbol_row:
                # Paired convention: use the preceding category row name
                if inferred_symbol is None:
                    inferred_symbol = label
                indicator_name = pending_indicator or label
                pending_indicator = None
            else:
                # Standalone row: the label IS the indicator name
                indicator_name = label
                pending_indicator = None

            if indicator_name:
                parsed: dict[str, Optional[float]] = {}
                for y, v in year_vals.items():
                    try:
                        parsed[y] = float(v) if pd.notna(v) and str(v).strip() not in ("", "nan") else None
                    except (ValueError, TypeError):
                        parsed[y] = None
                indicator_data[indicator_name] = parsed

    # ── 3. Resolve symbol ─────────────────────────────────────────────────
    resolved_symbol = (symbol or inferred_symbol or "UNKNOWN").upper()

    # ── 4. Build wide DataFrame  (one row per year) ───────────────────────
    records: list[dict] = []
    for year in year_cols:
        record: dict = {"symbol": resolved_symbol, "year": year}
        for db_col, vi_names in _INDICATOR_COLUMNS.items():
            value = None
            for vi_name in vi_names:
                value = indicator_data.get(vi_name, {}).get(year)
                if value is not None:
                    break
            record[db_col] = value
        records.append(record)

    df = pd.DataFrame(records)

    # Drop years where every indicator is NaN (sparse trailing years)
    indicator_cols = list(_INDICATOR_COLUMNS.keys())
    df = df.dropna(subset=indicator_cols, how="all").reset_index(drop=True)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Balance Sheet / Income Statement / Cash Flow – simple wide-format CSVs
# ─────────────────────────────────────────────────────────────────────────────

_BALANCE_SHEET_MAP: dict[str, str] = {
    "TỔNG TÀI SẢN":                           "total_assets",
    "TÀI SẢN NGẮN HẠN":                       "current_assets",
    "Tiền và tương đương tiền":               "cash_and_equivalents",
    "Giá trị thuần đầu tư ngắn hạn":          "short_term_investments_net",
    "Các khoản phải thu":                     "accounts_receivable",
    "Hàng tồn kho, ròng":                     "inventory_net",
    "TÀI SẢN DÀI HẠN":                        "long_term_assets",
    "Tài sản cố định":                        "fixed_assets",
    "Đầu tư dài hạn":                         "long_term_investments",
    "NỢ PHẢI TRẢ":                             "total_liabilities",
    "Nợ ngắn hạn":                            "current_liabilities",
    "Phải trả người bán":                     "accounts_payable",
    "Vay ngắn hạn":                           "short_term_loans",
    "Nợ dài hạn":                             "long_term_liabilities",
    "Vay dài hạn":                            "long_term_loans",
    "VỐN CHỦ SỞ HỮU":                         "equity",
    "Vốn góp":                                "paid_in_capital",
    "Lãi chưa phân phối":                     "retained_earnings",
    "TỔNG CỘNG NGUỒN VỐN":                    "total_liabilities_and_equity",
}

_INCOME_STATEMENT_MAP: dict[str, str] = {
    "Doanh số":                                        "gross_revenue",
    "Doanh số thuần":                                  "net_revenue",
    "Giá vốn hàng bán":                               "cogs",
    "Lãi gộp":                                        "gross_profit",
    "Thu nhập tài chính":                             "financial_income",
    "Chi phí tài chính":                              "financial_expense",
    "Trong đó: Chi phí lãi vay":                     "interest_expense",
    "Chi phí bán hàng":                               "selling_expense",
    "Chi phí quản lý doanh  nghiệp":                  "admin_expense",
    "Lãi/(lỗ) từ hoạt động kinh doanh":              "operating_profit",
    "Lãi/(lỗ) ròng trước thuế":                      "profit_before_tax",
    "Chi phí thuế thu nhập doanh nghiệp":             "income_tax_expense",
    "Lãi/(lỗ) thuần sau thuế":                       "net_profit_after_tax",
    "Lợi nhuận của Cổ đông của Công ty mẹ":          "net_income_parent",
    "Lãi cơ bản trên cổ phiếu":                      "eps_basic",
    "EBIT":                                            "ebit",
    "EBITDA":                                          "ebitda",
}

_CASH_FLOW_MAP: dict[str, str] = {
    "Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh": "cfo",
    "Lãi/lỗ trước những thay đổi vốn lưu động":                   "profit_before_wc_changes",
    "Lãi trước thuế":                                              "profit_before_tax_cf",
    "Khấu hao TSCĐ":                                               "depreciation",
    "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư":               "cfi",
    "Tiền mua tài sản cố định và các tài sản dài hạn khác":       "capex",
    "Cổ tức và tiền lãi nhận được":                               "dividends_received",
    "Lưu chuyển tiền tệ từ hoạt động tài chính":                 "cff",
    "Tiền thu từ phát hành cổ phiếu và vốn góp":                 "proceeds_from_share_issuance",
    "Tiền thu được các khoản đi vay":                             "proceeds_from_loans",
    "Tiển trả các khoản đi vay":                                  "repayment_of_loans",
    "Cổ tức đã trả":                                              "dividends_paid",
    "Lưu chuyển tiền thuần trong kỳ":                            "net_cash_change",
    "Tiền và tương đương tiền đầu kỳ":                           "cash_beginning",
    "Tiền và tương đương tiền cuối kỳ":                          "cash_ending",
}


def _process_wide_csv(
    csv_path: str,
    column_map: dict[str, str],
    symbol: Optional[str] = None,
) -> pd.DataFrame:
    """
    Parse a wide-format financial CSV (label in col-0, years in remaining cols)
    and return a tidy DataFrame with one row per (symbol, year).

    The symbol is inferred from the filename stem (everything before the first '_')
    when not provided explicitly.

    Parameters
    ──────────
    csv_path   : path to the CSV file
    column_map : mapping of Vietnamese label → output column name
    symbol     : override symbol; inferred from filename if None

    Returns
    ───────
    pd.DataFrame with columns: symbol, year, <mapped columns>
    """
    raw = pd.read_csv(csv_path, header=0, dtype=str)

    # Identify year columns
    year_cols = [c for c in raw.columns if re.match(r'^20[12]\d$', str(c).strip())]
    if not year_cols:
        raise ValueError(f"No year columns found in {csv_path}")

    label_col = raw.columns[0]

    # Infer symbol from filename when not supplied
    if symbol is None:
        stem = os.path.splitext(os.path.basename(csv_path))[0]  # e.g. VNM_balance_sheet
        symbol = stem.split("_")[0].upper()

    # Index rows by label for quick lookup
    row_index: dict[str, dict[str, Optional[float]]] = {}
    for _, row in raw.iterrows():
        label = str(row[label_col]).strip() if pd.notna(row[label_col]) else ""
        if not label:
            continue
        parsed: dict[str, Optional[float]] = {}
        for y in year_cols:
            v = row[y]
            try:
                parsed[y] = float(v) if pd.notna(v) and str(v).strip() not in ("", "nan") else None
            except (ValueError, TypeError):
                parsed[y] = None
        row_index[label] = parsed

    # Build one record per year
    records: list[dict] = []
    for year in year_cols:
        record: dict = {"symbol": symbol, "year": year}
        for vi_name, db_col in column_map.items():
            record[db_col] = row_index.get(vi_name, {}).get(year)
        records.append(record)

    df = pd.DataFrame(records)

    # Drop years where every mapped column is NaN
    mapped_cols = list(column_map.values())
    df = df.dropna(subset=mapped_cols, how="all").reset_index(drop=True)
    return df


def process_balance_sheet_csv(
    csv_path: str,
    symbol: Optional[str] = None,
) -> pd.DataFrame:
    """
    Parse a *_balance_sheet.csv from SSI iBoard and return a tidy DataFrame
    with one row per (symbol, year).

    Mapped columns (see _BALANCE_SHEET_MAP):
        total_assets, current_assets, cash_and_equivalents,
        short_term_investments_net, accounts_receivable, inventory_net,
        long_term_assets, fixed_assets, long_term_investments,
        total_liabilities, current_liabilities, accounts_payable,
        short_term_loans, long_term_liabilities, long_term_loans,
        equity, paid_in_capital, retained_earnings,
        total_liabilities_and_equity
    """
    return _process_wide_csv(csv_path, _BALANCE_SHEET_MAP, symbol)


def process_income_statement_csv(
    csv_path: str,
    symbol: Optional[str] = None,
) -> pd.DataFrame:
    """
    Parse a *_income_statement.csv from SSI iBoard and return a tidy DataFrame
    with one row per (symbol, year).

    Mapped columns (see _INCOME_STATEMENT_MAP):
        gross_revenue, net_revenue, cogs, gross_profit,
        financial_income, financial_expense, interest_expense,
        selling_expense, admin_expense, operating_profit,
        profit_before_tax, income_tax_expense, net_profit_after_tax,
        net_income_parent, eps_basic, ebit, ebitda
    """
    return _process_wide_csv(csv_path, _INCOME_STATEMENT_MAP, symbol)


def process_cash_flow_csv(
    csv_path: str,
    symbol: Optional[str] = None,
) -> pd.DataFrame:
    """
    Parse a *_cash_flow.csv from SSI iBoard and return a tidy DataFrame
    with one row per (symbol, year).

    Mapped columns (see _CASH_FLOW_MAP):
        cfo, profit_before_wc_changes, profit_before_tax_cf, depreciation,
        cfi, capex, dividends_received,
        cff, proceeds_from_share_issuance, proceeds_from_loans,
        repayment_of_loans, dividends_paid,
        net_cash_change, cash_beginning, cash_ending
    """
    return _process_wide_csv(csv_path, _CASH_FLOW_MAP, symbol)


# Substrings seen in Selenium WebDriverException messages when the Chrome
# tab/session has died and navigation can no longer recover on its own.
_BROWSER_DEAD_SIGNATURES = (
    "tab crashed",
    "invalid session id",
    "no such window",
    "chrome not reachable",
    "disconnected",
    "session deleted",
)


def is_browser_dead(exc: Exception) -> bool:
    """True if *exc* indicates the Chrome tab/session crashed and needs a restart."""
    msg = str(exc).lower()
    return any(sig in msg for sig in _BROWSER_DEAD_SIGNATURES)


def _wait_for_new_download(download_dir: str, before_mtime: float, timeout: int = DOWNLOAD_WAIT_SEC) -> Optional[str]:
    """
    Poll *download_dir* until a file newer than *before_mtime* appears
    (and is no longer a .crdownload / .tmp partial file).
    Returns the final file path, or None on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        candidates = glob.glob(os.path.join(download_dir, "*"))
        for fpath in candidates:
            if not os.path.isfile(fpath):
                continue
            if fpath.endswith((".crdownload", ".tmp", ".part")):
                continue  # still downloading
            if os.path.getmtime(fpath) > before_mtime:
                return fpath
        time.sleep(0.5)
    return None


# ─────────────────────────────────────────────────────────────
# Crawler
# ─────────────────────────────────────────────────────────────

class SSIFinancialDownloader:
    def __init__(self, download_dir: str, headless: bool = False):
        load_dotenv()
        self.username = os.getenv("SSI_USERNAME")
        self.password = os.getenv("SSI_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("SSI_USERNAME and SSI_PASSWORD must be set in .env file")

        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)

        self.options = Options()
        if headless:
            self.options.add_argument("--headless=new")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--start-maximized")

        # Tell Chrome where to save downloaded files automatically
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        self.options.add_experimental_option("prefs", prefs)

        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    # ── lifecycle ─────────────────────────────────────────────

    def start(self):
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 20)
        print(f"Browser started. Downloads → {self.download_dir}")

    def close(self):
        if self.driver:
            self.driver.quit()
            print("Browser closed.")

    def restart(self) -> bool:
        """Recover from a crashed/dead tab: quit, relaunch, and log back in."""
        print("[RECOVER] Restarting browser session …")
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.driver = None
        self.start()
        return self.login()

    # ── login ─────────────────────────────────────────────────

    def login(self) -> bool:
        print("Logging in to SSI iBoard …")
        self.driver.get(LOGIN_URL)
        time.sleep(3)

        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.ID, "btnToLoginSSO")))
            btn.click()
            time.sleep(3)
        except TimeoutException:
            pass

        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "txt-username")))
        password_field = self.driver.find_element(By.ID, "txt-password")

        username_field.clear()
        username_field.send_keys(self.username)
        time.sleep(0.4)
        password_field.clear()
        password_field.send_keys(self.password)
        time.sleep(0.4)

        submit = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login[type='submit']")
        submit.click()

        try:
            self.wait.until(lambda d: "login" not in d.current_url.lower())
            print("Login successful.")
            time.sleep(3)
            return True
        except TimeoutException:
            print("Login failed or timed out.")
            return False

    # ── navigation ────────────────────────────────────────────

    def go_to_fundamental_analysis(self):
        print(f"Navigating to {BASE_URL} …")
        self.driver.get(BASE_URL)
        time.sleep(4)

    # ── symbol search (inside iframe) ─────────────────────────

    def search_symbol(self, symbol: str) -> bool:
        """
        Search using the contenteditable ticker div recorded from DevTools.
        Steps mirror the recording exactly:
          1. click the ticker div to open the search filter
          2. set innerHTML on the contenteditable div + fire 'input' event
          3. click the first dropdown result (span.w-20)
        """
        print(f"Searching for symbol in iframe: {symbol}")
        try:
            # Step 1: open search
            ticker = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.lm_items > div:nth-of-type(1) div.ticker")
                )
            )
            self.driver.execute_script("arguments[0].click();", ticker)
            time.sleep(0.5)

            # Step 2: type symbol into contenteditable div
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "div.lm_items > div:nth-of-type(1) "
                     "div.search-filter-wrapper div.d-flex > div")
                )
            )
            self.driver.execute_script("arguments[0].innerHTML = '';", search_input)
            self.driver.execute_script(
                f"arguments[0].innerHTML = '{symbol.lower()}';", search_input
            )
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                search_input,
            )
            time.sleep(2)

            # Step 3: click first result
            first_result = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.w-20"))
            )
            self.driver.execute_script("arguments[0].click();", first_result)
            print(f"Selected symbol: {symbol}")
            time.sleep(3)
            return True

        except Exception as exc:
            print(f"Symbol search error: {exc}")
            import traceback
            traceback.print_exc()
            return False

    # ── iframe ────────────────────────────────────────────────

    def switch_to_iframe(self) -> bool:
        try:
            self.driver.switch_to.default_content()
            iframe = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "iframe[src*='fiin-app.ssi.com.vn']")
                )
            )
            self.driver.switch_to.frame(iframe)
            time.sleep(3)
            print("Switched into fiin-app iframe.")
            return True
        except Exception as exc:
            print(f"iframe switch error: {exc}")
            return False

    def switch_to_main(self):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

    # ── tab / click helpers ───────────────────────────────────

    def _click_css(self, selector: str, label: str, timeout: int = 10) -> bool:
        """Click an element by CSS selector (JS click for reliability)."""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            self.driver.execute_script("arguments[0].click();", el)
            print(f"Clicked: {label}")
            time.sleep(2)
            return True
        except Exception as exc:
            print(f"[WARN] Could not click '{label}' ({selector}): {exc}")
            return False

    def _click_lm_tab(self, index: int, timeout: int = 10) -> bool:
        """
        Click a Golden Layout outer tab by 0-based index.
        GoldenLayout uses mousedown, so we dispatch a real mousedown+click
        via JS rather than a synthetic click().
        """
        try:
            deadline = time.time() + timeout
            tabs = []
            while time.time() < deadline:
                tabs = self.driver.find_elements(By.CSS_SELECTOR, "ul.lm_tabs li.lm_tab")
                if tabs:
                    break
                time.sleep(0.5)

            print(f"Found {len(tabs)} lm_tabs")
            for i, t in enumerate(tabs):
                print(f"  tab[{i}]: {t.get_attribute('title') or t.text.strip()[:40]}")

            if not tabs or index >= len(tabs):
                print(f"[WARN] Tab index {index} out of range (found {len(tabs)} tabs)")
                return False

            tab = tabs[index]

            # Dispatch mousedown + mouseup + click — GoldenLayout needs mousedown
            self.driver.execute_script("""
                var el = arguments[0];
                ['mousedown','mouseup','click'].forEach(function(type) {
                    el.dispatchEvent(new MouseEvent(type, {
                        bubbles: true, cancelable: true, view: window
                    }));
                });
            """, tab)
            print(f"Dispatched mousedown+click on lm_tab index {index}")
            time.sleep(2.5)
            return True
        except Exception as exc:
            print(f"[WARN] Could not click lm_tab index {index}: {exc}")
            return False

    # ── download helper ───────────────────────────────────────

    def _click_download_and_save(self, selector: str, label: str, dest_filename: str) -> bool:
        """
        Click the TẢI XUỐNG button, wait for the file, then rename it.
        Tries the given selector first; falls back to any visible
        a.btn-cus-nomal.bg-b-color-3 on the page.
        """
        existing = glob.glob(os.path.join(self.download_dir, "*"))
        before_mtime = max(
            (os.path.getmtime(f) for f in existing if os.path.isfile(f)), default=0.0
        )

        btn = None
        # Try the specific selector first
        for sel in [selector, "a.btn-cus-nomal.bg-b-color-3"]:
            try:
                candidates = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for c in candidates:
                    if c.is_displayed():
                        btn = c
                        break
                if btn:
                    break
            except Exception:
                continue

        if btn is None:
            print(f"[WARN] Download button not found for: {label}")
            return False

        print(f"Clicking TẢI XUỐNG for: {label}")
        self.driver.execute_script("arguments[0].click();", btn)

        downloaded = _wait_for_new_download(self.download_dir, before_mtime)
        if not downloaded:
            print(f"[WARN] Download timed out for: {label}")
            return False

        # Convert xlsx → csv if needed, otherwise just rename
        if downloaded.lower().endswith((".xlsx", ".xls")):
            if os.path.exists(dest_filename):
                os.remove(dest_filename)
            _xlsx_to_csv(downloaded, dest_filename)
            os.remove(downloaded)
        elif os.path.abspath(downloaded) != os.path.abspath(dest_filename):
            if os.path.exists(dest_filename):
                os.remove(dest_filename)
            os.rename(downloaded, dest_filename)

        print(f"Saved: {os.path.basename(dest_filename)}")
        return True

    # ── public API ────────────────────────────────────────────

    def download_financial_indicators(self, symbol: str) -> Optional[str]:
        """
        Download only the "Chỉ số tài chính" tab (Panel 2) for *symbol*.
        Assumes go_to_fundamental_analysis() → switch_to_iframe() →
        search_symbol() have already run. Returns the saved CSV path, or
        None on failure.
        """
        print("\n── Chỉ số tài chính ──")
        self._click_lm_tab(1)
        time.sleep(1.5)
        dest = os.path.join(self.download_dir, f"{symbol}_financial_indicators.csv")
        ok = self._click_download_and_save(
            "div.lm_items > div:nth-of-type(2) span > span", "Chỉ số tài chính", dest
        )
        return dest if ok else None

    def download_financial_indicators_for_symbol(self, symbol: str) -> Optional[str]:
        """
        Navigate to fundamental-analysis, search *symbol*, and download only
        the "Chỉ số tài chính" tab — skips Cân đối kế toán / Kết quả kinh
        doanh / Lưu chuyển tiền tệ entirely, since those tabs never carry
        bank-only indicators.
        """
        symbol = symbol.upper().strip()

        self.go_to_fundamental_analysis()

        if not self.switch_to_iframe():
            print("Could not switch into iframe. Aborting.")
            return None

        if not self.search_symbol(symbol):
            print(f"Could not load symbol: {symbol}")
            return None
        time.sleep(2)

        return self.download_financial_indicators(symbol)

    def download_all(self, symbol: str) -> dict:
        """
        Download all report sheets for *symbol* using selectors from the
        DevTools recording.

        Layout (Golden Layout panels inside the iframe):
          Panel 1  →  Báo cáo tài chính  (sub-tabs: li 1/2/3)
          Panel 2  →  Chỉ số tài chính   (own download btn)

        Download button = the inner <span> of the TẢI XUỐNG anchor in each panel.
        """
        symbol = symbol.upper().strip()
        results: dict = {}

        self.go_to_fundamental_analysis()

        if not self.switch_to_iframe():
            print("Could not switch into iframe. Aborting.")
            return results

        if not self.search_symbol(symbol):
            print(f"Could not load symbol: {symbol}")
            return results
        time.sleep(2)

        # ── Panel 1, sub-tab 1: Cân đối kế toán ──────────────
        print("\n── Cân đối kế toán ──")
        self._click_css(
            "div.lm_items > div:nth-of-type(1) li:nth-of-type(1) span",
            "Cân đối kế toán",
        )
        time.sleep(1.5)
        dest = os.path.join(self.download_dir, f"{symbol}_balance_sheet.csv")
        ok = self._click_download_and_save(
            "div.lm_items > div:nth-of-type(1) span > span", "Cân đối kế toán", dest
        )
        results["Cân đối kế toán"] = dest if ok else None
        time.sleep(1)

        # ── Panel 1, sub-tab 2: Kết quả kinh doanh ───────────
        print("\n── Kết quả kinh doanh ──")
        self._click_css(
            "div.lm_items li:nth-of-type(2) span",
            "Kết quả kinh doanh",
        )
        time.sleep(1.5)
        dest = os.path.join(self.download_dir, f"{symbol}_income_statement.csv")
        ok = self._click_download_and_save(
            "div.lm_items > div:nth-of-type(1) span > span", "Kết quả kinh doanh", dest
        )
        results["Kết quả kinh doanh"] = dest if ok else None
        time.sleep(1)

        # ── Panel 1, sub-tab 3: Lưu chuyển tiền tệ ───────────
        print("\n── Lưu chuyển tiền tệ ──")
        self._click_css(
            "li:nth-of-type(3) > a",
            "Lưu chuyển tiền tệ",
        )
        time.sleep(1.5)
        dest = os.path.join(self.download_dir, f"{symbol}_cash_flow.csv")
        ok = self._click_download_and_save(
            "div.lm_items > div:nth-of-type(1) span > span", "Lưu chuyển tiền tệ", dest
        )
        results["Lưu chuyển tiền tệ"] = dest if ok else None
        time.sleep(1)

        # ── Panel 2: Chỉ số tài chính ─────────────────────────
        results["Chỉ số tài chính"] = self.download_financial_indicators(symbol)
        time.sleep(1)

        return results


# ─────────────────────────────────────────────────────────────
# Process downloaded CSVs → cleaned, renamed output
# ─────────────────────────────────────────────────────────────

def process_all_csvs(
    output_dir: str,
    symbol: Optional[str] = None,
    processed_dir: Optional[str] = None,
) -> dict:
    """
    Find the four raw CSVs in *output_dir* and run all four processors.
    Saves the tidy results as *_processed.csv files.

    Parameters
    ──────────
    output_dir    : folder containing the raw downloaded CSVs
    symbol        : stock symbol override (inferred from filenames when None)
    processed_dir : folder to write processed files (defaults to output_dir)

    Returns
    ───────
    dict mapping sheet name → saved path (or None on failure)
    """
    if processed_dir is None:
        processed_dir = output_dir
    os.makedirs(processed_dir, exist_ok=True)

    # Infer symbol from any matching file when not given
    if symbol is None:
        for f in glob.glob(os.path.join(output_dir, "*_financial_indicators.csv")):
            symbol = os.path.basename(f).split("_")[0].upper()
            break
    if symbol is None:
        for f in glob.glob(os.path.join(output_dir, "*_balance_sheet.csv")):
            symbol = os.path.basename(f).split("_")[0].upper()
            break
    if symbol is None:
        symbol = "UNKNOWN"

    processors = [
        (
            "financial_indicators",
            os.path.join(output_dir, f"{symbol}_financial_indicators.csv"),
            process_financial_indicators_csv,
        ),
        (
            "balance_sheet",
            os.path.join(output_dir, f"{symbol}_balance_sheet.csv"),
            process_balance_sheet_csv,
        ),
        (
            "income_statement",
            os.path.join(output_dir, f"{symbol}_income_statement.csv"),
            process_income_statement_csv,
        ),
        (
            "cash_flow",
            os.path.join(output_dir, f"{symbol}_cash_flow.csv"),
            process_cash_flow_csv,
        ),
    ]

    results: dict = {}
    for name, src_path, processor in processors:
        if not os.path.exists(src_path):
            print(f"  [SKIP] {os.path.basename(src_path)} not found")
            results[name] = None
            continue
        try:
            df = processor(src_path, symbol=symbol)
            dest_path = src_path  # overwrite the raw file with the processed version
            df.to_csv(dest_path, index=False, encoding="utf-8-sig")
            print(f"  [OK]   {os.path.basename(dest_path)}  ({len(df)} rows, {len(df.columns)} cols)")
            results[name] = dest_path
        except Exception as exc:
            print(f"  [ERROR] {name}: {exc}")
            results[name] = None

    return results


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download SSI financial report files. Downloads all symbols by default."
    )
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
        help="Directory where downloaded/processed files are saved (default: ./output)",
    )
    parser.add_argument(
        "--symbol", "-s",
        default=None,
        help="Download a single symbol only (e.g. --symbol VNM). Omit to download all symbols.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode",
    )
    parser.add_argument(
        "--process-only",
        action="store_true",
        help="Skip downloading; only (re-)process already-downloaded CSVs in --output."
             " Processes the single --symbol if given, otherwise all symbols in progress file.",
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Clear the download progress file and start from scratch.",
    )
    args = parser.parse_args()

    # ── resolve symbol list ───────────────────────────────────
    if args.symbol:
        symbols = [args.symbol.upper().strip()]
    else:
        try:
            symbols = _load_all_symbols()
        except Exception as exc:
            print(f"[ERROR] Could not load symbol list: {exc}")
            sys.exit(1)

    # ── process-only mode ─────────────────────────────────────
    if args.process_only:
        print(f"Processing CSVs in: {args.output}")
        for sym in symbols:
            csv_exists = any(
                os.path.exists(os.path.join(args.output, f"{sym}_{sheet}.csv"))
                for sheet in ("balance_sheet", "income_statement", "cash_flow", "financial_indicators")
            )
            if not csv_exists:
                continue
            print(f"\n{'=' * 60}")
            print(f"Processing: {sym}")
            print("=" * 60)
            process_all_csvs(args.output, symbol=sym)
        return

    # ── reset progress if requested ───────────────────────────
    if args.reset_progress and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("Progress file cleared.")

    done = _load_progress()
    remaining = [s for s in symbols if s.upper() not in done]

    print(f"Total symbols      : {len(symbols)}")
    print(f"Already completed  : {len(done)}")
    print(f"Remaining to crawl : {len(remaining)}")

    if not remaining:
        print("All symbols have already been downloaded.")
        return

    downloader = SSIFinancialDownloader(download_dir=args.output, headless=args.headless)
    try:
        downloader.start()
        if not downloader.login():
            print("Login failed. Exiting.")
            sys.exit(1)

        for idx, symbol in enumerate(remaining, start=1):
            print(f"\n{'=' * 60}")
            print(f"[{idx}/{len(remaining)}] Downloading: {symbol}")
            print("=" * 60)

            try:
                results = downloader.download_all(symbol)

                success = any(p and os.path.exists(p) for p in results.values())
                if not success:
                    print(f"[WARN] No files downloaded for {symbol} — skipping.")
                    continue

                # Print per-sheet status
                for sheet, path in results.items():
                    status = f"✅  {os.path.basename(path)}" if path and os.path.exists(path) else "❌  failed"
                    print(f"  {sheet:<30} {status}")

                # Process CSVs immediately after download
                print(f"\nProcessing {symbol} CSVs …")
                process_all_csvs(args.output, symbol=symbol)

                _mark_done(symbol)
                print(f"✅  {symbol} done")

            except Exception as exc:
                print(f"[ERROR] {symbol}: {exc}")
                import traceback
                traceback.print_exc()

                if is_browser_dead(exc):
                    try:
                        downloader.restart()
                    except Exception as restart_exc:
                        print(f"[FATAL] Could not restart browser: {restart_exc}")
                        break

                print(f"Skipping {symbol} and continuing …")
                continue

        print(f"\n{'=' * 60}")
        print("ALL DONE")
        print(f"{'=' * 60}")
        print(f"Completed: {len(_load_progress())} / {len(symbols)} symbols")

    except Exception as exc:
        print(f"Fatal error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        downloader.close()


if __name__ == "__main__":
    main()
