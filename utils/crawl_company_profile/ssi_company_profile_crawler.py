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

When running in database mode, the crawler reads symbols from BI_Profile
and updates profile/contact fields that need refresh.

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
import traceback
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _collapse_whitespace(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    collapsed = re.sub(r"\s+", " ", text).strip()
    return collapsed if collapsed else None


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

    def _get_selected_profile_panel(self) -> Optional[object]:
        """Return the currently active panel inside #company-profile-info."""
        panels = self.driver.find_elements(
            By.CSS_SELECTOR,
            "#company-profile-info .company-profile-subtask[data-headlessui-state='selected']"
        )
        return panels[0] if panels else None

    def _extract_company_basic_rows(self, panel, field_map: Dict[str, tuple]) -> Dict:
        """Extract rows from .company-basic-info using a Vietnamese label map."""
        info: Dict = {}
        rows = panel.find_elements(By.CSS_SELECTOR, ".company-basic-info")

        for row in rows:
            divs = row.find_elements(By.XPATH, "./div")
            if len(divs) < 2:
                continue

            label = divs[0].text.strip()
            value = divs[1].text.strip()

            for vn_label, (key, dtype) in field_map.items():
                if vn_label not in label:
                    continue
                if dtype == 'float':
                    info[key] = _clean_number(value)
                elif dtype == 'int':
                    info[key] = _clean_int(value)
                else:
                    info[key] = value
                break

        return info

    def _scroll_window_to_load_more(self, steps: int = 8, pause: float = 0.6) -> None:
        """Scroll the page so lazy-rendered cards/rows can mount."""
        last_height = -1
        for _ in range(steps):
            try:
                height = self.driver.execute_script("return document.body.scrollHeight") or 0
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause)
                if height == last_height:
                    break
                last_height = height
            except Exception:
                break

    def _scroll_scrollable_descendants(self, root, rounds: int = 8, pause: float = 0.6) -> None:
        """Scroll any overflow container inside a section until its rendered content stabilizes."""
        last_marker = None
        for _ in range(rounds):
            try:
                marker = self.driver.execute_script(
                    """
                    const root = arguments[0];
                    const nodes = [root, ...root.querySelectorAll('*')].filter((el) => {
                        const style = window.getComputedStyle(el);
                        const overflowY = style.overflowY || style.overflow;
                        return /(auto|scroll)/.test(overflowY) && el.scrollHeight > el.clientHeight + 2;
                    });
                    nodes.forEach((el) => { el.scrollTop = el.scrollHeight; });
                    return nodes.map((el) => `${el.scrollHeight}:${el.scrollTop}`).join('|');
                    """,
                    root,
                )
                self._scroll_window_to_load_more(steps=2, pause=0.25)
                time.sleep(pause)
                if marker == last_marker:
                    break
                last_marker = marker
            except Exception:
                break

    def _scroll_to_extract_all_table_rows(self, container, max_rounds: int = 20) -> List[Dict]:
        """
        Scroll through a virtual table, capturing all rows at each position.
        Deduplicates by (company_name, sub_symbol) to avoid virtual scroll artifacts.
        Returns list of extracted row dicts.
        """
        seen_keys = set()
        all_records = []
        last_count = -1
        stable_rounds = 0

        for round_num in range(max_rounds):
            try:
                tbody = container.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                for row in tbody:
                    try:
                        tds = row.find_elements(By.TAG_NAME, "td")
                        if len(tds) < 4:
                            continue
                        
                        company_name = tds[0].text.strip()
                        sub_symbol = tds[1].text.strip()
                        
                        if not company_name or not sub_symbol:
                            continue
                        
                        key = (company_name, sub_symbol)
                        if key not in seen_keys:
                            seen_keys.add(key)
                            all_records.append({
                                'company_name':            company_name,
                                'sub_symbol':              sub_symbol,
                                'charter_capital_billion': _clean_number(tds[2].text.strip()),
                                'ownership_pct':           _clean_number(tds[3].text.strip().replace('%', '')),
                            })
                    except Exception:
                        pass

                current_count = len(seen_keys)
                
                if current_count == last_count:
                    stable_rounds += 1
                    if stable_rounds >= 3:
                        break
                else:
                    stable_rounds = 0
                    last_count = current_count

                scroll_containers = container.find_elements(By.CSS_SELECTOR, ".scrollbar-container")
                for sc in scroll_containers:
                    self.driver.execute_script("arguments[0].scrollTop += 1000;", sc)

                time.sleep(0.5)
            except Exception as exc:
                print(f"Extract rows round {round_num} error: {exc}")
                break

        return all_records

    def _scroll_to_extract_all_leaders(self, container, max_rounds: int = 20) -> List[Dict]:
        """
        Scroll through a virtual leader list, capturing all leaders at each position.
        Deduplicates by (full_name, position) to avoid virtual scroll artifacts.
        Returns list of extracted leader dicts.
        """
        seen_keys = set()
        all_leaders = []
        last_count = -1
        stable_rounds = 0

        for round_num in range(max_rounds):
            try:
                groups = container.find_elements(By.CSS_SELECTOR, ".leader-group")
                
                for group in groups:
                    try:
                        paras = group.find_elements(By.TAG_NAME, "p")
                        if len(paras) >= 2:
                            full_name = paras[0].text.strip()
                            position = paras[1].text.strip()
                            
                            if not full_name or not position:
                                continue
                            
                            key = (full_name, position)
                            if key not in seen_keys:
                                seen_keys.add(key)
                                all_leaders.append({
                                    'full_name': full_name,
                                    'position':  position,
                                })
                    except Exception:
                        pass

                current_count = len(seen_keys)
                
                if current_count == last_count:
                    stable_rounds += 1
                    if stable_rounds >= 3:
                        break
                else:
                    stable_rounds = 0
                    last_count = current_count

                scroll_containers = container.find_elements(By.CSS_SELECTOR, ".scrollbar-container")
                for sc in scroll_containers:
                    self.driver.execute_script("arguments[0].scrollTop += 1000;", sc)

                time.sleep(0.5)
            except Exception as exc:
                print(f"Extract leaders round {round_num} error: {exc}")
                break

        return all_leaders

    # ── section extractors ───────────────────────────────────

    def _get_intro_tab(self) -> Dict:
        """Extract data from the 'Giới thiệu' tab."""
        info: Dict = {}
        try:
            self._click_tab_in_panel("#company-profile-info", "Giới thiệu")
            time.sleep(1.5)

            panel = self._get_selected_profile_panel()
            if not panel:
                return info

            # Overview text
            try:
                overview = panel.find_element(By.CSS_SELECTOR, ".company-over-view")
                info['description'] = _collapse_whitespace(overview.text)
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
                                if key == "website":
                                    try:
                                        anchor = spans[1].find_element(By.TAG_NAME, "a")
                                        href = _normalize_text(anchor.get_attribute("href"))
                                        info[key] = href or value
                                    except Exception:
                                        info[key] = value
                                else:
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

            panel = self._get_selected_profile_panel()
            if not panel:
                return info

            field_map = {
                'Mã SIC':             ('sic_code',               'str'),
                'Tên ngành':          ('industry_name',          'str'),
                'Mã ngành ICB':       ('icb_code',               'str'),
                'Năm thành lập':      ('founded_date',           'str'),
                'VĐL':                ('charter_capital_billion', 'float'),
                'Số lượng nhân viên': ('employee_count',         'int'),
                'Số lượng chi nhánh': ('branch_count',           'int'),
            }

            info.update(self._extract_company_basic_rows(panel, field_map))

        except Exception as exc:
            print(f"Basic info tab error: {exc}")

        return info

    def _get_listing_info_tab(self) -> Dict:
        """Extract data from the 'TT niêm yết' tab."""
        info: Dict = {}
        try:
            self._click_tab_in_panel("#company-profile-info", "TT niêm yết")
            time.sleep(1.5)

            panel = self._get_selected_profile_panel()
            if not panel:
                return info

            field_map = {
                'Ngày niêm yết':    ('listing_date',     'str'),
                'Nơi niêm yết':     ('exchange',          'str'),
                'Giá chào sàn':     ('ipo_price',         'float'),
                'KL đang niêm yết': ('listed_volume',     'int'),
                'Thị giá vốn':      ('market_cap_billion','float'),
                'SLCP lưu hành':    ('shares_outstanding','int'),
            }

            info.update(self._extract_company_basic_rows(panel, field_map))

        except Exception as exc:
            print(f"Listing info tab error: {exc}")

        return info

    def _get_leaders(self) -> List[Dict]:
        """Extract leadership data from 'Ban lãnh đạo' section."""
        try:
            panel = self.driver.find_element(By.ID, "leader-company")
            self._scroll_window_to_load_more()
            self._scroll_scrollable_descendants(panel)
            
            # Scroll and collect all leader data during scrolling
            leaders = self._scroll_to_extract_all_leaders(panel)
            print(f"  Leaders collected: {len(leaders)} unique")
            
            return leaders
        except Exception as exc:
            print(f"Leaders extraction error: {exc}")
            return []

    def _get_subsidiaries(self) -> List[Dict]:
        """Extract Công ty con + Công ty liên kết from the sub-company section."""
        all_records = []

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

                self._scroll_window_to_load_more()
                self._scroll_scrollable_descendants(active_panels[0])
                
                # Scroll and collect all row data during scrolling
                rows = self._scroll_to_extract_all_table_rows(active_panels[0])
                print(f"  {rel_type} collected: {len(rows)} unique")
                
                # Add relationship type to each record
                for row in rows:
                    row['relationship_type'] = rel_type
                    all_records.append(row)
                        
            except Exception as exc:
                print(f"Subsidiary table error ({rel_type}): {exc}")

        _parse_sub_table("sub-company", "subsidiary")
        _parse_sub_table("sub-company", "associate")

        return all_records

    def _get_stock_id(self, symbol: str) -> Optional[str]:
        """Lookup stock_id from Stock table by symbol."""
        try:
            result = (
                supabase.table("Stock")
                .select("id")
                .eq("stock_symbol", symbol.upper())
                .limit(1)
                .execute()
            )
            rows = result.data or []
            if rows:
                return rows[0].get("id")
            print(f"  Warning: No Stock entry found for {symbol}")
            return None
        except Exception as exc:
            print(f"  Stock lookup error for {symbol}: {exc}")
            return None

    def _update_profile_row(self, profile: Dict) -> bool:
        """Update contact fields, description, and key profile metrics in BI_Profile."""
        symbol = (profile.get("symbol") or "").strip().upper()
        if not symbol:
            return False

        try:
            current_result = (
                supabase.table("BI_Profile")
                .select(
                    "description,email,phone,website,fax,"
                    "sic_code,industry_name,icb_code,founded_date,"
                    "charter_capital_billion,employee_count,branch_count,"
                    "listing_date,exchange,ipo_price,listed_volume,"
                    "market_cap_billion,shares_outstanding"
                )
                .eq("symbol", symbol)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            print(f"BI_Profile lookup error for {symbol}: {exc}")
            return False

        current_row = (current_result.data or [{}])[0]
        payload = {}

        for field in ("email", "phone", "website", "fax"):
            current_value = _normalize_text(current_row.get(field))
            new_value = _normalize_text(profile.get(field))
            if new_value and not current_value:
                payload[field] = new_value

        current_description = _normalize_text(current_row.get("description"))
        new_description = _normalize_text(profile.get("description"))
        if new_description:
            should_refresh_description = False
            if not current_description:
                should_refresh_description = True
            else:
                longer_enough = len(new_description) > len(current_description) + 20
                significantly_longer = len(current_description) > 0 and len(new_description) >= int(len(current_description) * 1.2)
                should_refresh_description = longer_enough or significantly_longer

            if should_refresh_description:
                payload["description"] = new_description

        # Refresh structured profile fields when crawled data is present and differs.
        text_fields = (
            "sic_code",
            "industry_name",
            "icb_code",
            "founded_date",
            "listing_date",
            "exchange",
        )
        float_fields = (
            "charter_capital_billion",
            "ipo_price",
            "market_cap_billion",
        )
        int_fields = (
            "employee_count",
            "branch_count",
            "listed_volume",
            "shares_outstanding",
        )

        for field in text_fields:
            new_value = _normalize_text(profile.get(field))
            current_value = _normalize_text(current_row.get(field))
            if new_value and new_value != current_value:
                payload[field] = new_value

        for field in float_fields:
            new_value = profile.get(field)
            current_value = current_row.get(field)
            if new_value is None:
                continue
            try:
                new_float = float(new_value)
            except (TypeError, ValueError):
                continue

            current_float = None
            if current_value is not None:
                try:
                    current_float = float(current_value)
                except (TypeError, ValueError):
                    current_float = None

            if current_float is None or abs(new_float - current_float) > 1e-9:
                payload[field] = new_float

        for field in int_fields:
            new_value = profile.get(field)
            current_value = current_row.get(field)
            if new_value is None:
                continue
            try:
                new_int = int(new_value)
            except (TypeError, ValueError):
                continue

            current_int = None
            if current_value is not None:
                try:
                    current_int = int(current_value)
                except (TypeError, ValueError):
                    current_int = None

            if current_int is None or new_int != current_int:
                payload[field] = new_int

        if not payload:
            return False

        try:
            result = (
                supabase.table("BI_Profile")
                .update(payload)
                .eq("symbol", symbol)
                .execute()
            )
            updated_rows = getattr(result, "data", None) or []
            if updated_rows:
                print(f"  Updated BI_Profile fields for {symbol}: {', '.join(payload.keys())}")
                return True

            print(f"  No BI_Profile row updated for {symbol}")
            return False
        except Exception as exc:
            print(f"  BI_Profile update error for {symbol}: {exc}")
            return False

    def _insert_leaders(self, stock_id: str, leaders: List[Dict]) -> bool:
        """Delete old leaders for stock_id and insert new ones."""
        if not stock_id or not leaders:
            return True
        
        try:
            # Delete old leaders
            supabase.table("BI_Leader").delete().eq("stock_id", stock_id).execute()
            
            # Insert new leaders
            records = [
                {
                    "stock_id": stock_id,
                    "full_name": leader.get("full_name"),
                    "position": leader.get("position"),
                }
                for leader in leaders
            ]
            result = supabase.table("BI_Leader").insert(records).execute()
            inserted = len(getattr(result, "data", []) or [])
            print(f"  Inserted {inserted} leaders for stock_id {stock_id[:8]}…")
            return True
        except Exception as exc:
            print(f"  BI_Leader insert error for stock_id {stock_id[:8]}…: {exc}")
            return False

    def _insert_subsidiaries(self, stock_id: str, subsidiaries: List[Dict]) -> bool:
        """Delete old subsidiaries for stock_id and insert new ones."""
        if not stock_id or not subsidiaries:
            return True
        
        try:
            # Delete old subsidiaries
            supabase.table("BI_Subsidiary").delete().eq("stock_id", stock_id).execute()
            
            # Insert new subsidiaries
            records = [
                {
                    "stock_id": stock_id,
                    "company_name": sub.get("company_name"),
                    "sub_symbol": sub.get("sub_symbol"),
                    "charter_capital_billion": sub.get("charter_capital_billion"),
                    "ownership_pct": sub.get("ownership_pct"),
                    "relationship_type": sub.get("relationship_type"),
                }
                for sub in subsidiaries
            ]
            result = supabase.table("BI_Subsidiary").insert(records).execute()
            inserted = len(getattr(result, "data", []) or [])
            print(f"  Inserted {inserted} subsidiaries/associates for stock_id {stock_id[:8]}…")
            return True
        except Exception as exc:
            print(f"  BI_Subsidiary insert error for stock_id {stock_id[:8]}…: {exc}")
            return False

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
    Read symbols from BI_Profile and return a filtered list of stock symbols,
    excluding any symbol that ends with 4 or more digits
    (i.e. bond / derivative instruments such as CACB2502, BAB122032, …).
    """
    try:
        symbols: List[str] = []
        page = 0
        page_size = 1000

        while True:
            offset = page * page_size
            result = (
                supabase.table("BI_Profile")
                .select("symbol")
                .offset(offset)
                .limit(page_size)
                .execute()
            )
            rows = result.data or []
            if not rows:
                break

            for row in rows:
                symbol = _normalize_text(row.get("symbol"))
                if symbol:
                    symbols.append(symbol.upper())

            if len(rows) < page_size:
                break

            page += 1

        filtered = [s for s in symbols if not re.search(r'\d{4,}$', s)]
        return sorted(set(filtered))
    except Exception as exc:
        raise RuntimeError(f"Could not load symbol list from BI_Profile: {exc}") from exc


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


def main(force: bool = False):
    """Batch crawl all symbols from BI_Profile and update database tables.
    
    Args:
        force: If True, crawl all symbols and overwrite existing data.
               If False, skip symbols in crawl_progress.txt.
    """
    symbols = _load_all_symbols()
    done = _load_progress()

    if force:
        remaining = symbols
        print(f"Force mode: crawling all {len(symbols)} symbols and overwriting data.")
    else:
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

                # ── Get stock_id for this symbol ──
                stock_id = crawler._get_stock_id(symbol)
                if not stock_id:
                    print(f"  Skipping {symbol}: no Stock entry found")
                    _mark_done(symbol)
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
                    for sub in result['subsidiaries'][:5]:
                        print(f"  [{sub['relationship_type']:10s}] {sub['sub_symbol']:8s} {sub['company_name']} ({sub['ownership_pct']}%)")
                    if len(result['subsidiaries']) > 5:
                        print(f"  … and {len(result['subsidiaries']) - 5} more")

                # ── Update database tables ──
                print("\nUpdating database…")
                crawler._update_profile_row(result["profile"])
                crawler._insert_leaders(stock_id, result['leaders'])
                crawler._insert_subsidiaries(stock_id, result['subsidiaries'])

                # ── mark as done so restarts skip it ──
                _mark_done(symbol)
                print(f"✓ {symbol} completed and marked done.")

            except Exception as exc:
                print(f"  ERROR crawling {symbol}: {exc}")
                traceback.print_exc()

    finally:
        crawler.close()
        print("\nBrowser closed.")
        print("Batch crawl completed.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default=None, help="Crawl a single symbol only, e.g. VHM")
    parser.add_argument("--force", action="store_true", help="Crawl all symbols and overwrite existing data")
    args = parser.parse_args()

    if args.symbol:
        crawler = SSICompanyProfileCrawler(headless=False)
        try:
            symbol = args.symbol.strip().upper()
            print(f"Crawling single symbol: {symbol}")
            result = crawler.crawl(symbol)

            if result.get('profile'):
                # Get stock_id
                stock_id = crawler._get_stock_id(symbol)
                if stock_id:
                    print("\nUpdating database…")
                    crawler._update_profile_row(result["profile"])
                    crawler._insert_leaders(stock_id, result['leaders'])
                    crawler._insert_subsidiaries(stock_id, result['subsidiaries'])
                    print(f"✓ {symbol} completed and database updated.")
                else:
                    print(f"No Stock entry found for {symbol}, skipping database update.")
            else:
                print(f"No data collected for {symbol}.")
        finally:
            crawler.close()
            print("Browser closed.")
    else:
        main(force=args.force)
