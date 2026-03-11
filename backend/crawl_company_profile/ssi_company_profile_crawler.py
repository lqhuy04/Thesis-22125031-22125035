"""
SSI iBoard Company Profile Crawler
Crawls company profile data from:
  https://iboard.ssi.com.vn/analysis/company-profile

Data collected per symbol
──────────────────────────
Tab "Giới thiệu"   → description, address, email, phone, website, fax
Tab "TT cơ bản"    → SIC code, industry, ICB code, founded date,
                      charter capital, employee count, branch count
Tab "TT niêm yết"  → listing date, exchange, IPO price, listed volume,
                      market cap, shares outstanding
"Ban lãnh đạo"     → leader name + position
"Công ty con"      → subsidiaries (name, code, capital, ownership %)
"Công ty liên kết" → associates  (name, code, capital, ownership %)

Output
──────
  <SYMBOL>_company_profile.csv
  <SYMBOL>_leaders.csv
  <SYMBOL>_subsidiaries.csv
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _clean_number(text: str) -> Optional[float]:
    """Convert Vietnamese-formatted number string to float."""
    if not text or text.strip() in ('', '--', 'N/A'):
        return None
    cleaned = text.strip().replace(',', '').replace(' ', '')
    # Remove trailing unit labels like "Tỷ"
    cleaned = re.sub(r'[^\d.\-]', '', cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_int(text: str) -> Optional[int]:
    val = _clean_number(text)
    return int(val) if val is not None else None


# ──────────────────────────────────────────────────────────────
# Crawler
# ──────────────────────────────────────────────────────────────

class SSICompanyProfileCrawler:
    """Crawl company profile data from SSI iBoard."""

    LOGIN_URL   = "https://iboard.ssi.com.vn/auth/login"
    PROFILE_URL = "https://iboard.ssi.com.vn/analysis/company-profile"

    def __init__(self, headless: bool = False):
        load_dotenv()
        self.username = os.getenv('SSI_USERNAME')
        self.password = os.getenv('SSI_PASSWORD')
        if not self.username or not self.password:
            raise ValueError("SSI_USERNAME and SSI_PASSWORD must be set in .env file")

        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--start-maximized')

        self.driver: Optional[webdriver.Chrome] = None
        self.wait:   Optional[WebDriverWait]    = None
        self._logged_in: bool = False

    # ── lifecycle ────────────────────────────────────────────

    def start(self):
        self.driver = webdriver.Chrome(options=self.options)
        self.wait   = WebDriverWait(self.driver, 20)

    def close(self):
        if self.driver:
            self.driver.quit()

    # ── authentication ───────────────────────────────────────

    def login(self) -> bool:
        print("Logging in to SSI iBoard …")
        self.driver.get(self.LOGIN_URL)
        time.sleep(3)

        # Click "Đăng nhập" button if present
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.ID, "btnToLoginSSO")))
            btn.click()
            time.sleep(3)
        except TimeoutException:
            pass  # already on the form

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
            self.wait.until(
                lambda d: "login" not in d.current_url.lower()
            )
            print("Login successful.")
            time.sleep(3)
            return True
        except TimeoutException:
            print("Login may have failed.")
            return False

    # ── iframe ────────────────────────────────────────────────

    def switch_to_iframe(self) -> bool:
        """
        Switch Selenium context into the fiin-app iframe that contains
        #stock-detail and all profile content.
        """
        try:
            print("Looking for fiin-app iframe…")
            self.driver.switch_to.default_content()

            # Try selectors in priority order (avoid the inner TradingView iframe)
            selectors = [
                "iframe[src*='fiin-app.ssi.com.vn']",
                "iframe[src*='iboard.ssi.com.vn'][src*='stock-detail']",
                "iframe[src*='iboard.ssi.com.vn'][src*='company']",
            ]
            for sel in selectors:
                frames = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if frames:
                    self.driver.switch_to.frame(frames[0])
                    time.sleep(3)
                    print(f"Switched to iframe ({sel}).")
                    return True

            # Fallback: pick the largest non-tradingview iframe on the page
            all_frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for f in all_frames:
                src = f.get_attribute("src") or ""
                if "tradingview" in src.lower():
                    continue  # skip the chart iframe
                if "ssi" in src.lower() or "fiin" in src.lower():
                    self.driver.switch_to.frame(f)
                    time.sleep(3)
                    print(f"Switched to fallback iframe: {src[:80]}")
                    return True

            print("No suitable iframe found on page.")
            return False
        except Exception as exc:
            print(f"Iframe switch error: {exc}")
            return False

    def switch_to_main(self):
        """Switch back to the top-level page context."""
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

    # ── symbol search (inside iframe) ────────────────────────

    def search_symbol(self, symbol: str) -> bool:
        """
        Search for a stock symbol using the input inside the iframe
        (#stock-detail-custom-select-stock-input).
        Must be called while the driver context is already inside the iframe.
        """
        print(f"Searching for symbol in iframe: {symbol}")
        time.sleep(2)
        try:
            search_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.ID, "stock-detail-custom-select-stock-input")
                )
            )
            search_input.click()
            time.sleep(0.3)
            # Clear and type the symbol
            search_input.send_keys(Keys.CONTROL + "a")
            search_input.send_keys(Keys.DELETE)
            search_input.clear()
            time.sleep(0.2)
            search_input.send_keys(symbol)
            time.sleep(2)  # wait for dropdown to populate

            # Wait for the dropdown list to appear
            dropdown_menu = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.ID, "stock-detail-custom-select-stock-menu")
                )
            )
            items = dropdown_menu.find_elements(By.TAG_NAME, "li")
            if not items:
                # Try role=option or any child
                items = dropdown_menu.find_elements(By.CSS_SELECTOR, "li, [role='option'], .stock-item")

            if items:
                # Click the first matching result
                self.driver.execute_script("arguments[0].click();", items[0])
                print(f"Selected symbol: {symbol}")
                time.sleep(4)  # wait for data to reload
                return True

            # Fallback: press Enter if dropdown is empty but input has the value
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            print(f"Symbol sent via Enter: {symbol}")
            return True

        except Exception as exc:
            print(f"Symbol search error: {exc}")
            import traceback
            traceback.print_exc()
            return False

    # ── top-level page tab ─────────────────────────────────────

    def _switch_to_ho_so_tab(self) -> bool:
        """
        Click the top-level 'Hồ sơ' tab (id='tab_companyProfile').
        This must be done before any profile sub-section is accessible.
        """
        try:
            tab_li = self.wait.until(
                EC.presence_of_element_located((By.ID, "tab_companyProfile"))
            )
            tab_a = tab_li.find_element(By.TAG_NAME, "a")
            self.driver.execute_script("arguments[0].click();", tab_a)
            print("Switched to top-level tab: Hồ sơ")
            time.sleep(3)
            return True
        except Exception as exc:
            print(f"Could not switch to Hồ sơ tab: {exc}")
            return False

    # ── tab helpers ──────────────────────────────────────────

    def _click_tab_in_panel(self, panel_selector: str, tab_label: str) -> bool:
        """
        Click a tab button whose text *contains* tab_label,
        inside the element matched by panel_selector.
        """
        try:
            panel = self.driver.find_element(By.CSS_SELECTOR, panel_selector)
            buttons = panel.find_elements(By.CSS_SELECTOR, "[role='tab']")
            for btn in buttons:
                if tab_label in (btn.text.strip() or btn.get_attribute("aria-label") or ""):
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                    return True
        except Exception as exc:
            print(f"Tab click error ({tab_label}): {exc}")
        return False

    def _wait_for_tab_panel(self, panel_id: str, timeout: int = 8) -> bool:
        """Wait for a tab-panel to become visible (not display:none / hidden)."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_element(By.ID, panel_id).get_attribute("data-headlessui-state") == "selected"
            )
            return True
        except Exception:
            return False

    # ── section extractors ───────────────────────────────────

    def _get_intro_tab(self) -> Dict:
        """Extract data from the 'Giới thiệu' tab."""
        info: Dict = {}
        try:
            self._click_tab_in_panel("#company-profile-info", "Giới thiệu")
            time.sleep(1.5)

            # Find the currently active tab panel (avoid hardcoded headlessui IDs)
            panels = self.driver.find_elements(
                By.CSS_SELECTOR,
                "#company-profile-info .company-profile-subtask[data-headlessui-state='selected']"
            )
            if not panels:
                return info
            panel = panels[0]

            # Overview text
            try:
                overview = panel.find_element(By.CSS_SELECTOR, ".company-over-view")
                info['description'] = overview.text.strip()
            except NoSuchElementException:
                info['description'] = None

            # Contact list items
            contact_map = {
                'Địa chỉ':    'address',
                'Email':       'email',
                'Điện thoại': 'phone',
                'Website':     'website',
                'Fax':         'fax',
            }
            try:
                items = panel.find_elements(By.CSS_SELECTOR, ".company-contact li")
                for li in items:
                    spans = li.find_elements(By.TAG_NAME, "span")
                    if len(spans) >= 2:
                        label = spans[0].text.strip().rstrip(':').strip()
                        value = spans[1].text.strip()
                        for vn_label, key in contact_map.items():
                            if vn_label in label:
                                info[key] = value
                                break
            except Exception:
                pass

        except Exception as exc:
            print(f"Intro tab error: {exc}")

        return info

    def _get_basic_info_tab(self) -> Dict:
        """Extract data from the 'TT cơ bản' tab."""
        info: Dict = {}
        try:
            self._click_tab_in_panel("#company-profile-info", "TT cơ bản")
            time.sleep(1.5)

            # Try to locate the visible panel for TT cơ bản
            panels = self.driver.find_elements(
                By.CSS_SELECTOR,
                "#company-profile-info .company-profile-subtask[data-headlessui-state='selected']"
            )
            if not panels:
                return info
            panel = panels[0]

            field_map = {
                'Mã SIC':             ('sic_code',               'str'),
                'Tên ngành':          ('industry_name',          'str'),
                'Mã ngành ICB':       ('icb_code',               'str'),
                'Năm thành lập':      ('founded_date',           'str'),
                'VĐL':                ('charter_capital_billion', 'float'),
                'Số lượng nhân viên': ('employee_count',         'int'),
                'Số lượng chi nhánh': ('branch_count',           'int'),
            }

            rows = panel.find_elements(By.CSS_SELECTOR, ".company-basic-info")
            for row in rows:
                divs = row.find_elements(By.XPATH, "./div")
                if len(divs) < 2:
                    continue
                label = divs[0].text.strip()
                value = divs[1].text.strip()
                for vn_label, (key, dtype) in field_map.items():
                    if vn_label in label:
                        if dtype == 'float':
                            info[key] = _clean_number(value)
                        elif dtype == 'int':
                            info[key] = _clean_int(value)
                        else:
                            info[key] = value
                        break

        except Exception as exc:
            print(f"Basic info tab error: {exc}")

        return info

    def _get_listing_info_tab(self) -> Dict:
        """Extract data from the 'TT niêm yết' tab."""
        info: Dict = {}
        try:
            self._click_tab_in_panel("#company-profile-info", "TT niêm yết")
            time.sleep(1.5)

            panels = self.driver.find_elements(
                By.CSS_SELECTOR,
                "#company-profile-info .company-profile-subtask[data-headlessui-state='selected']"
            )
            if not panels:
                return info
            panel = panels[0]

            field_map = {
                'Ngày niêm yết':    ('listing_date',     'str'),
                'Nơi niêm yết':     ('exchange',          'str'),
                'Giá chào sàn':     ('ipo_price',         'float'),
                'KL đang niêm yết': ('listed_volume',     'int'),
                'Thị giá vốn':      ('market_cap_billion','float'),
                'SLCP lưu hành':    ('shares_outstanding','int'),
            }

            rows = panel.find_elements(By.CSS_SELECTOR, ".company-basic-info")
            for row in rows:
                divs = row.find_elements(By.XPATH, "./div")
                if len(divs) < 2:
                    continue
                label = divs[0].text.strip()
                value = divs[1].text.strip()
                for vn_label, (key, dtype) in field_map.items():
                    if vn_label in label:
                        if dtype == 'float':
                            info[key] = _clean_number(value)
                        elif dtype == 'int':
                            info[key] = _clean_int(value)
                        else:
                            info[key] = value
                        break

        except Exception as exc:
            print(f"Listing info tab error: {exc}")

        return info

    def _get_leaders(self) -> List[Dict]:
        """Extract leadership data from 'Ban lãnh đạo' section."""
        leaders = []
        try:
            panel = self.driver.find_element(By.ID, "leader-company")
            groups = panel.find_elements(By.CSS_SELECTOR, ".leader-group")
            for group in groups:
                try:
                    paras = group.find_elements(By.TAG_NAME, "p")
                    if len(paras) >= 2:
                        full_name = paras[0].text.strip()
                        position  = paras[1].text.strip()
                        # Skip empty rows (invisible / placeholder divs)
                        if full_name and position:
                            leaders.append({
                                'full_name': full_name,
                                'position':  position,
                            })
                except Exception:
                    continue
        except Exception as exc:
            print(f"Leaders extraction error: {exc}")
        return leaders

    def _get_subsidiaries(self) -> List[Dict]:
        """Extract Công ty con + Công ty liên kết from the sub-company section."""
        records = []

        def _parse_sub_table(container_id: str, rel_type: str):
            try:
                panel = self.driver.find_element(By.ID, container_id)
                self._click_tab_in_panel(f"#{container_id}", "Công ty con" if rel_type == "subsidiary" else "Công ty liên kết")
                time.sleep(1)

                # Find the active tab panel
                active_panels = panel.find_elements(
                    By.CSS_SELECTOR,
                    ".company-profile-subtask[data-headlessui-state='selected']"
                )
                if not active_panels:
                    active_panels = panel.find_elements(By.CSS_SELECTOR, ".company-profile-subtask")
                if not active_panels:
                    return

                tbody = active_panels[0].find_elements(By.CSS_SELECTOR, "tbody tr")
                for row in tbody:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) < 4:
                        continue
                    records.append({
                        'company_name':            tds[0].text.strip(),
                        'sub_symbol':              tds[1].text.strip(),
                        'charter_capital_billion': _clean_number(tds[2].text.strip()),
                        'ownership_pct':           _clean_number(tds[3].text.strip().replace('%', '')),
                        'relationship_type':       rel_type,
                    })
            except Exception as exc:
                print(f"Subsidiary table error ({rel_type}): {exc}")

        _parse_sub_table("sub-company", "subsidiary")
        _parse_sub_table("sub-company", "associate")

        return records

    def _get_company_name(self) -> str:
        """
        Extract the company name shown in the stock-detail header.
        Inside the iframe: <div class="flex-none font-bold pt-1">Company Name</div>
        Falls back to .company-name for compatibility.
        """
        # Primary: the company name next to the search box inside #stock-detail-header
        for selector in [
            "#stock-detail-header .flex-none.font-bold",
            "#stock-detail-header .font-bold",
            ".company-name",
        ]:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                name = elem.text.strip()
                if name:
                    if '/' in name:
                        name = name.split('/')[0].strip()
                    return name
            except Exception:
                continue
        return ""

    # ── main crawl entry point ───────────────────────────────

    def crawl(self, symbol: str) -> Dict:
        """
        Crawl all company profile data for *symbol*.
        Returns a dict with keys:
          'profile'      → dict  (one row for company_profiles table)
          'leaders'      → list  (rows for company_leaders table)
          'subsidiaries' → list  (rows for company_subsidiaries table)
        """
        result: Dict = {'profile': {}, 'leaders': [], 'subsidiaries': []}

        if not self.driver:
            self.start()

        if not self._logged_in:
            if not self.login():
                print("Login failed.")
                return result
            self._logged_in = True

            print(f"Navigating to {self.PROFILE_URL} …")
            self.driver.get(self.PROFILE_URL)
            time.sleep(5)

            # ── switch into the iframe that hosts #stock-detail ──
            iframe_ok = self.switch_to_iframe()
            if not iframe_ok:
                print("Warning: no iframe found – attempting to work on main page context.")
        else:
            # Already logged in – switch back into the iframe context
            # (it may have been lost after the previous symbol's extraction)
            self.switch_to_main()
            iframe_ok = self.switch_to_iframe()
            if not iframe_ok:
                print("Warning: could not re-enter iframe for symbol search.")

        # ── search for the symbol inside the iframe ──
        if not self.search_symbol(symbol):
            print(f"Could not load symbol {symbol}.")
            # Don't abort – the iframe may already show a default symbol

        # ── click the top-level 'Hồ sơ' tab ──
        if not self._switch_to_ho_so_tab():
            print("Warning: could not switch to Hồ sơ tab, continuing anyway…")

        company_name = self._get_company_name()
        print(f"Company: {company_name}")

        # ── profile info ──
        profile: Dict = {
            'symbol':       symbol.upper(),
            'company_name': company_name,
            'data_source':  'SSI iBoard',
        }
        profile.update(self._get_intro_tab())
        profile.update(self._get_basic_info_tab())
        profile.update(self._get_listing_info_tab())

        result['profile']      = profile
        result['leaders']      = self._get_leaders()
        result['subsidiaries'] = self._get_subsidiaries()

        print(f"Profile fields collected : {len(profile)}")
        print(f"Leaders collected        : {len(result['leaders'])}")
        print(f"Subsidiaries/associates  : {len(result['subsidiaries'])}")

        return result


# ──────────────────────────────────────────────────────────────
# Export helpers
# ──────────────────────────────────────────────────────────────

def export_to_csv(result: Dict, symbol: str, output_dir: str = ".") -> None:
    """Save crawl results to CSV files ready for PostgreSQL import."""
    os.makedirs(output_dir, exist_ok=True)
    sym = symbol.upper()

    # company_profiles
    profile_df = pd.DataFrame([result['profile']])
    profile_path = os.path.join(output_dir, f"{sym}_company_profile.csv")
    profile_df.to_csv(profile_path, index=False, encoding='utf-8-sig')
    print(f"Saved: {profile_path}")

    # company_leaders
    if result['leaders']:
        leaders_df = pd.DataFrame(result['leaders'])
        leaders_df.insert(0, 'symbol', sym)
        leaders_path = os.path.join(output_dir, f"{sym}_leaders.csv")
        leaders_df.to_csv(leaders_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {leaders_path}")
    else:
        print("No leaders data to save.")

    # company_subsidiaries
    if result['subsidiaries']:
        subs_df = pd.DataFrame(result['subsidiaries'])
        subs_df.insert(0, 'symbol', sym)
        subs_path = os.path.join(output_dir, f"{sym}_subsidiaries.csv")
        subs_df.to_csv(subs_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {subs_path}")
    else:
        print("No subsidiaries/associates data to save.")


def print_postgresql_import(symbol: str) -> None:
    sym = symbol.upper()
    print(f"""
-- Import commands for PostgreSQL:

\\COPY company_profiles(symbol, company_name, description, address, email, phone, website, fax,
     sic_code, industry_name, icb_code, founded_date, charter_capital_billion,
     employee_count, branch_count, listing_date, exchange, ipo_price, listed_volume,
     market_cap_billion, shares_outstanding, data_source)
FROM '{sym}_company_profile.csv' DELIMITER ',' CSV HEADER;

\\COPY company_leaders(symbol, full_name, position)
FROM '{sym}_leaders.csv' DELIMITER ',' CSV HEADER;

\\COPY company_subsidiaries(symbol, company_name, sub_symbol, charter_capital_billion, ownership_pct, relationship_type)
FROM '{sym}_subsidiaries.csv' DELIMITER ',' CSV HEADER;
""")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def _load_all_symbols() -> List[str]:
    """
    Read all_symbols_raw.txt (same directory) and return a filtered list of
    stock symbols, excluding any symbol that ends with 4 or more digits
    (i.e. bond / derivative instruments such as CACB2502, BAB122032, …).
    """
    symbols_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_symbols_raw.txt")
    content = ""
    with open(symbols_file, encoding="utf-8-sig", errors="replace") as f:
        try:
            content = f.read()
        except UnicodeDecodeError:
            pass

    # Retry with utf-16 if utf-8-sig failed (file starts with 0xFF 0xFE BOM)
    if not content or content.startswith('\x00') or '\ufffd' in content[:20]:
        with open(symbols_file, encoding="utf-16") as f:
            content = f.read()

    # The file contains a Python-list literal on one of its lines
    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find symbol list in all_symbols_raw.txt")

    raw_list: List[str] = eval(match.group())            # safe: known file format
    filtered = [s for s in raw_list if not re.search(r'\d{4,}$', s)]
    return filtered


PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawl_progress.txt")


def _load_progress() -> set:
    """Return the set of symbols already successfully crawled."""
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def _mark_done(symbol: str) -> None:
    """Append a symbol to the progress file."""
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(symbol.upper() + "\n")


def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    symbols = _load_all_symbols()
    done = _load_progress()

    remaining = [s for s in symbols if s.upper() not in done]
    print(f"Total symbols      : {len(symbols)}")
    print(f"Already completed  : {len(done)}")
    print(f"Remaining to crawl : {len(remaining)}")

    if not remaining:
        print("All symbols have already been crawled.")
        return

    crawler = SSICompanyProfileCrawler(headless=False)
    try:
        for idx, symbol in enumerate(remaining, start=1):
            print(f"\n[{idx}/{len(remaining)}] Crawling {symbol} …")
            try:
                result = crawler.crawl(symbol)

                if not result['profile']:
                    print(f"  No data collected for {symbol}, skipping.")
                    continue

                # ── print summary ──
                print("\n" + "=" * 60)
                print(f"PROFILE SUMMARY – {symbol}")
                print("=" * 60)
                for k, v in result['profile'].items():
                    if k != 'description':
                        print(f"  {k:32s}: {v}")

                if result['leaders']:
                    print(f"\nLeadership ({len(result['leaders'])} persons):")
                    for ldr in result['leaders'][:5]:
                        print(f"  {ldr['full_name']:30s} – {ldr['position']}")
                    if len(result['leaders']) > 5:
                        print(f"  … and {len(result['leaders']) - 5} more")

                if result['subsidiaries']:
                    print(f"\nSubsidiaries / Associates ({len(result['subsidiaries'])} entries):")
                    for sub in result['subsidiaries']:
                        print(f"  [{sub['relationship_type']:10s}] {sub['sub_symbol']:8s} {sub['company_name']} ({sub['ownership_pct']}%)")

                # ── export CSVs ──
                export_to_csv(result, symbol, output_dir)

                # ── mark as done so restarts skip it ──
                _mark_done(symbol)

            except Exception as exc:
                print(f"  ERROR crawling {symbol}: {exc}")
                import traceback
                traceback.print_exc()

    finally:
        crawler.close()
        print("Browser closed.")


if __name__ == "__main__":
    main()
