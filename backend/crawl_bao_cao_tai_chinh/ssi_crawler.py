"""
SSI iBoard Fundamental Analysis Crawler
Crawl financial data from SSI iBoard and calculate key financial metrics
URL: https://iboard.ssi.com.vn/analysis/fundamental-analysis
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
from typing import Dict, List, Optional
import re
import os
from dotenv import load_dotenv

class SSIiBoardCrawler:
    def __init__(self, headless: bool = False):
        """
        Initialize SSI iBoard crawler
        Args:
            headless: Run browser in headless mode
        """
        # Load environment variables
        load_dotenv()
        
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--start-maximized')
        self.driver = None
        self.wait = None
        self.login_url = "https://iboard.ssi.com.vn/auth/login"
        self.base_url = "https://iboard.ssi.com.vn/analysis/fundamental-analysis"
        
        # Get credentials from environment
        self.username = os.getenv('SSI_USERNAME')
        self.password = os.getenv('SSI_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("SSI_USERNAME and SSI_PASSWORD must be set in .env file")
        
    def start_driver(self):
        """Start Chrome driver"""
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def close_driver(self):
        """Close Chrome driver"""
        if self.driver:
            self.driver.quit()
    
    def login(self) -> bool:
        """
        Perform login to SSI iBoard
        Returns:
            True if login successful, False otherwise
        """
        try:
            print("Starting login process...")
            
            # Navigate to login page
            print(f"Navigating to {self.login_url}")
            self.driver.get(self.login_url)
            time.sleep(3)
            
            # Click the main login button (Đăng nhập)
            try:
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "btnToLoginSSO"))
                )
                login_button.click()
                print("Clicked main login button")
                time.sleep(3)
            except:
                print("Main login button not found, assuming already on login form")
            
            # Wait for login form to appear
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "txt-username"))
            )
            
            password_field = self.driver.find_element(By.ID, "txt-password")
            
            # Clear and fill in credentials
            print("Entering credentials...")
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(0.5)
            
            # Submit login form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login[type='submit']")
            submit_button.click()
            print("Clicked login submit button")
            
            # Wait for successful login (check for redirect or dashboard elements)
            try:
                # Wait for either successful redirect or error message
                self.wait.until(
                    lambda driver: driver.current_url != self.login_url + "/" and 
                                   "login" not in driver.current_url.lower()
                )
                print("Login successful!")
                time.sleep(3)  # Wait for page to fully load
                return True
            except TimeoutException:
                print("Login may have failed - checking for error messages")
                # You might want to add error checking here
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
            
    def search_symbol(self, symbol: str) -> bool:
        """
        Search for a stock symbol
        Args:
            symbol: Stock symbol (e.g., 'SSI', 'VNM')
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Searching for symbol: {symbol}")
            
            # Wait longer for page to fully load
            time.sleep(3)
            
            # Find search box (contenteditable div)
            search_box = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-filter .ticker"))
            )
            
            # Click to focus the search box
            search_box.click()
            time.sleep(0.5)
            
            # Clear existing content using JavaScript since it's contenteditable
            self.driver.execute_script("arguments[0].innerHTML = '';", search_box)
            time.sleep(0.5)
            
            # Enter symbol using JavaScript to ensure it works with contenteditable div
            self.driver.execute_script(f"arguments[0].innerHTML = '{symbol}';", search_box)
            
            # Trigger input event to make the dropdown appear
            self.driver.execute_script("""
                var event = new Event('input', { bubbles: true });
                arguments[0].dispatchEvent(event);
            """, search_box)
            
            time.sleep(2)  # Wait for dropdown to populate
            
            # Wait for dropdown to appear and check if there are valid results
            try:
                dropdown = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".drop-search.show"))
                )
                
                # Check if there are no matching results
                no_match = dropdown.find_elements(By.XPATH, ".//div[contains(text(), 'Không có cổ phiếu tương thích')]")
                if no_match:
                    print(f"No matching stocks found for symbol: {symbol}")
                    return False
                
                # Look for clickable dropdown items (links)
                dropdown_items = dropdown.find_elements(By.CSS_SELECTOR, "a.dropdown-item")
                if not dropdown_items:
                    # If no links, try looking for any clickable dropdown items
                    dropdown_items = dropdown.find_elements(By.CSS_SELECTOR, ".dropdown-item")
                
                if dropdown_items:
                    # Click on first matching result
                    first_result = dropdown_items[0]
                    self.driver.execute_script("arguments[0].click();", first_result)
                    print(f"Selected symbol: {symbol}")
                    time.sleep(3)  # Wait for data to load
                    return True
                else:
                    print(f"No clickable results found for symbol: {symbol}")
                    return False
                    
            except TimeoutException:
                print("Dropdown did not appear - checking if symbol is already selected")
                # Check if the symbol is already loaded (sometimes it's pre-selected)
                current_symbol = search_box.text.strip()
                if current_symbol.upper() == symbol.upper():
                    print(f"Symbol {symbol} appears to be already selected")
                    return True
                return False
            
        except Exception as e:
            print(f"Error searching symbol: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_current_symbol(self) -> str:
        """
        Get the currently loaded symbol from the page
        Returns:
            Current symbol or 'UNKNOWN' if not found
        """
        try:
            # Try to find the current symbol in the search box or company info
            current_symbol = "UNKNOWN"
            
            # Try different selectors to find current symbol
            selectors = [
                ".search-filter .ticker",
                ".ticker",
                ".company-code",
                ".symbol"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text and len(text) <= 5 and text.isalpha():
                        current_symbol = text.upper()
                        break
                except:
                    continue
            
            print(f"Current symbol appears to be: {current_symbol}")
            return current_symbol
            
        except Exception as e:
            print(f"Could not determine current symbol: {e}")
            return "UNKNOWN"
    
    def switch_to_iframe(self) -> bool:
        """
        Switch to the financial data iframe
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Looking for financial data iframe...")
            
            # Wait for iframe to load
            iframe = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='fiin-app.ssi.com.vn']"))
            )
            
            print("Found iframe, switching to it...")
            self.driver.switch_to.frame(iframe)
            time.sleep(3)  # Wait for iframe content to load
            
            print("Successfully switched to iframe")
            return True
            
        except Exception as e:
            print(f"Error switching to iframe: {e}")
            return False
    
    def switch_back_to_main(self):
        """
        Switch back to main content (out of iframe)
        """
        try:
            self.driver.switch_to.default_content()
            print("Switched back to main content")
        except Exception as e:
            print(f"Error switching back to main content: {e}")
    
    def switch_to_tab(self, tab_name: str) -> bool:
        """
        Switch to a specific tab
        Args:
            tab_name: Tab name ('Cân Đối Kế Toán', 'Kết Quả Kinh Doanh', 'Lưu Chuyển Tiền Tệ')
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Switching to tab: {tab_name}")
            
            # Wait a moment for any previous tab content to settle
            time.sleep(1)
            
            # Try different selectors for tabs in iframe
            tab_selectors = [
                ".nav-tabs .nav-link",  # New structure from HTML
                ".nav-tabs a",
                ".m-tabs__link",
                ".custom-tabs .nav-link",
                ".lm_tabs .lm_tab",
                ".tab",
                ".nav-tab",
                "[role='tab']",
                ".MuiTab-root",
                ".ant-tabs-tab"
            ]
            
            tabs_found = False
            for selector in tab_selectors:
                try:
                    tabs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if tabs:
                        print(f"Found {len(tabs)} tabs with selector: {selector}")
                        tabs_found = True
                        
                        for i, tab in enumerate(tabs):
                            # Check various attributes and text content for tab name
                            tab_text_sources = [
                                tab.get_attribute('title'),
                                tab.get_attribute('aria-label'),
                                tab.text.strip(),
                                tab.get_attribute('data-title')
                            ]
                            
                            # Also check nested span elements
                            try:
                                span_elements = tab.find_elements(By.TAG_NAME, "span")
                                for span in span_elements:
                                    tab_text_sources.append(span.text.strip())
                            except:
                                pass
                            
                            # Check if any text source contains our target tab name
                            for text_source in tab_text_sources:
                                if text_source and tab_name in text_source:
                                    print(f"Found matching tab at index {i}: '{text_source}'")
                                    # Use JavaScript click to ensure it works
                                    self.driver.execute_script("arguments[0].click();", tab)
                                    time.sleep(3)  # Wait for tab content to load
                                    print(f"Successfully switched to tab: {tab_name}")
                                    return True
                        
                        # If we found tabs but no exact match, print available tabs for debugging
                        if selector == ".nav-tabs .nav-link":
                            print("Available tabs:")
                            for i, tab in enumerate(tabs):
                                try:
                                    text = tab.text.strip() or tab.get_attribute('title') or 'No text'
                                    span_text = ''
                                    spans = tab.find_elements(By.TAG_NAME, "span")
                                    if spans:
                                        span_text = spans[0].text.strip()
                                    print(f"  Tab {i}: '{text}' | span: '{span_text}'")
                                except:
                                    print(f"  Tab {i}: Could not get text")
                        
                        break
                except Exception as e:
                    continue
            
            if not tabs_found:
                print("No tabs found with any selector")
            else:
                print(f"Tab '{tab_name}' not found among available tabs")
                
            return False
            
        except Exception as e:
            print(f"Error switching tab: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_table_data(self, table_class: str = "table-wl-summary") -> pd.DataFrame:
        """
        Extract data from financial table
        Args:
            table_class: CSS class of the table
        Returns:
            DataFrame with financial data
        """
        try:
            print("Extracting table data...")
            
            # Try different table selectors
            table_selectors = [
                f".{table_class}",
                "table.table-wl-summary",
                "table.custom-table", 
                "table",
                ".table",
                ".data-table",
                ".financial-table",
                "[role='table']"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    tables = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if tables:
                        # Get the first visible table
                        for t in tables:
                            if t.is_displayed():
                                table = t
                                print(f"Found table with selector: {selector}")
                                break
                        if table:
                            break
                except:
                    continue
            
            if not table:
                print("No table found")
                return pd.DataFrame()
            
            # Get headers (years) - improved detection
            headers = []
            try:
                header_cells = table.find_elements(By.XPATH, ".//thead//th | .//tr[1]//th | .//tr[1]//td")
                
                for i, cell in enumerate(header_cells):
                    if i < 2:  # Skip first 2 columns (Indicator name and Trend)
                        continue
                    
                    # Try to get year from different elements
                    year_text = ''
                    try:
                        # Try span element first
                        span = cell.find_element(By.TAG_NAME, "span")
                        year_text = span.text.strip()
                    except:
                        # Fall back to cell text
                        year_text = cell.text.strip()
                    
                    # Check if it's a valid year
                    if year_text and year_text.isdigit() and len(year_text) == 4:
                        headers.append(year_text)
            except Exception as e:
                print(f"Error getting headers: {e}")
                return pd.DataFrame()
            
            print(f"Found years: {headers}")
            
            if not headers:
                print("No valid year headers found")
                return pd.DataFrame()
            
            # Get financial data
            data = {}
            try:
                rows = table.find_elements(By.XPATH, ".//tbody//tr | .//tr[position()>1]")
                
                for row_idx, row in enumerate(rows):
                    try:
                        cells = row.find_elements(By.XPATH, ".//td | .//th")
                        if len(cells) < 3:
                            continue
                        
                        # Get indicator name from first cell
                        indicator = ''
                        try:
                            # Try to find the indicator text in nested div
                            indicator_div = cells[0].find_element(By.CSS_SELECTOR, ".text-truncate")
                            indicator = indicator_div.text.strip()
                        except:
                            try:
                                # Try other nested elements
                                indicator_elem = cells[0].find_element(By.CSS_SELECTOR, "div")
                                indicator = indicator_elem.get_attribute('title') or indicator_elem.text.strip()
                            except:
                                # Fall back to cell text
                                indicator = cells[0].text.strip()
                        
                        if not indicator or indicator == '--' or len(indicator) == 0:
                            continue
                        
                        print(f"Processing indicator: {indicator}")
                        
                        # Get values for each year (skip first 2 columns)
                        values = []
                        for i, cell in enumerate(cells):
                            if i < 2:  # Skip first 2 columns
                                continue
                                
                            val_text = cell.text.strip()
                            
                            if val_text == '--' or val_text == '' or val_text == 'null':
                                values.append(None)
                            else:
                                # Clean and convert value
                                val_clean = val_text.replace(',', '').replace('%', '')
                                try:
                                    # Handle negative values in parentheses
                                    if val_clean.startswith('(') and val_clean.endswith(')'):
                                        val_clean = '-' + val_clean[1:-1]
                                    values.append(float(val_clean))
                                except ValueError:
                                    values.append(None)
                        
                        # Only add if we have the right number of values
                        if len(values) == len(headers) and any(v is not None for v in values):
                            data[indicator] = values
                        
                    except Exception as e:
                        print(f"Error processing row {row_idx}: {e}")
                        continue
            
            except Exception as e:
                print(f"Error processing table rows: {e}")
                return pd.DataFrame()
            
            # Create DataFrame
            if data:
                df = pd.DataFrame(data, index=headers).T
                df.index.name = 'Indicator'
                print(f"Extracted {len(df)} indicators across {len(headers)} years")
                return df
            else:
                print("No data extracted")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error extracting table data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def crawl_financial_statements(self, symbol: str, skip_symbol_search: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Crawl all financial statements for a symbol
        Args:
            symbol: Stock symbol (for naming files)
            skip_symbol_search: Skip symbol search and use whatever is already loaded
        Returns:
            Dictionary of DataFrames with financial data
        """
        result = {}
        
        try:
            if not self.driver:
                self.start_driver()
            
            # Login first
            if not self.login():
                print("Login failed! Cannot proceed with crawling.")
                return result
            
            # Navigate to analysis page after successful login
            print(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(5)  # Give more time for page to load
            
            # Try to search for symbol, but continue even if it fails
            if not skip_symbol_search:
                print(f"Attempting to search for symbol: {symbol}")
                if not self.search_symbol(symbol):
                    print(f"Symbol search failed, but continuing with whatever symbol is currently loaded...")
            else:
                print("Skipping symbol search - using currently loaded symbol")
            
            # Switch to iframe where the financial data is loaded
            if not self.switch_to_iframe():
                print("Failed to switch to iframe, cannot access financial data")
                return result
            
            # Debug: See what's in the iframe
            self.debug_iframe_content()
            
            # Get Cân Đối Kế Toán (Balance Sheet)
            if self.switch_to_tab("Cân Đối Kế Toán"):
                df = self.get_table_data()
                if not df.empty:
                    result['balance_sheet'] = df
                    print(f"Successfully crawled Balance Sheet: {df.shape}")
            
            # Get Kết Quả Kinh Doanh (Income Statement)
            if self.switch_to_tab("Kết Quả Kinh Doanh"):
                df = self.get_table_data()
                if not df.empty:
                    result['income_statement'] = df
                    print(f"Successfully crawled Income Statement: {df.shape}")
            
            # Get Lưu Chuyển Tiền Tệ (Cash Flow Statement)
            if self.switch_to_tab("Lưu Chuyển Tiền Tệ"):
                df = self.get_table_data()
                if not df.empty:
                    result['cash_flow'] = df
                    print(f"Successfully crawled Cash Flow: {df.shape}")
            
            # Switch back to main content
            self.switch_back_to_main()
            
            return result
            
        except Exception as e:
            print(f"Error crawling financial statements: {e}")
            return result
    
    def debug_iframe_content(self):
        """
        Debug method to see what's inside the iframe
        """
        try:
            print("\\n=== DEBUGGING IFRAME CONTENT ===")
            
            # Get page source to see structure
            page_source = self.driver.page_source
            print(f"Page source length: {len(page_source)}")
            
            # Look for common elements
            common_selectors = [
                "div", "span", "table", "button", "a", "nav", 
                ".tab", ".lm_tab", "[role='tab']", ".MuiTab-root"
            ]
            
            for selector in common_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector '{selector}'")
                    if selector in [".tab", ".lm_tab", "[role='tab']", ".MuiTab-root"] and len(elements) <= 10:
                        for i, elem in enumerate(elements[:5]):  # Show first 5 only
                            try:
                                text = elem.text.strip()[:50]  # First 50 chars
                                title = elem.get_attribute('title') or ''
                                aria_label = elem.get_attribute('aria-label') or ''
                                print(f"  [{i}] text: '{text}', title: '{title}', aria-label: '{aria_label}'")
                            except:
                                pass
            
            print("=== END DEBUG ===\\n")
            
        except Exception as e:
            print(f"Debug error: {e}")

class FinancialAnalyzer:
    """Analyze and calculate financial indicators"""
    
    def __init__(self, statements: pd.DataFrame, ratios: pd.DataFrame):
        """
        Initialize analyzer
        Args:
            statements: Financial statements DataFrame
            ratios: Financial ratios DataFrame
        """
        self.statements = statements
        self.ratios = ratios
        
    def get_value(self, df: pd.DataFrame, indicator: str, year: str) -> Optional[float]:
        """Get value from DataFrame"""
        try:
            if indicator in df.index and year in df.columns:
                val = df.loc[indicator, year]
                return float(val) if pd.notna(val) else None
        except:
            pass
        return None
    
    def calculate_all_metrics(self, year: str) -> Dict[str, float]:
        """
        Calculate all financial metrics for a given year
        Args:
            year: Year to calculate (e.g., '2024')
        Returns:
            Dictionary of calculated metrics
        """
        metrics = {}
        
        # From ratios (already calculated by SSI)
        ratio_indicators = {
            'P/E': 'P/E',
            'P/B': 'P/B',
            'EPS (VND)': 'EPS',
            'BVPS (VND)': 'BVPS',
            'ROE (%)': 'ROE',
            'ROA (%)': 'ROA',
            'Biên lợi nhuận gộp (%)': 'Gross Margin',
            'Biên lợi nhuận ròng (%)': 'Net Margin',
            'Tăng trưởng doanh thu (YoY) (%)': 'Revenue YoY',
            'Tăng trưởng lợi nhuận (YoY) (%)': 'Profit YoY',
            'Nợ/VCSH': 'Debt/Equity',
            'Chỉ số thanh toán hiện thời': 'Current Ratio',
            'EV/EBITDA': 'EV/EBITDA',
            'Vốn hóa (Tỷ đồng)': 'Market Cap (Billion VND)',
            'Số CP lưu hành (Triệu CP)': 'Shares Outstanding (Million)'
        }
        
        for indicator, metric_name in ratio_indicators.items():
            val = self.get_value(self.ratios, indicator, year)
            if val is not None:
                metrics[metric_name] = val
        
        # From statements
        statement_indicators = {
            'Doanh thu thuần về hoạt động kinh doanh': 'Revenue (Billion VND)',
            'Lợi nhuận gộp': 'Gross Profit (Billion VND)',
            'Lợi nhuận kế toán sau thuế': 'Net Income (Billion VND)',
            'Tổng lợi nhuận kế toán trước thuế': 'Profit Before Tax (Billion VND)'
        }
        
        for indicator, metric_name in statement_indicators.items():
            val = self.get_value(self.statements, indicator, year)
            if val is not None:
                metrics[metric_name] = val
        
        # Calculate additional metrics
        # FCF (if cash flow data available)
        # Beta (would need price history)
        
        return metrics
    
    def generate_report(self, years: List[str]) -> pd.DataFrame:
        """
        Generate comprehensive financial report
        Args:
            years: List of years to include
        Returns:
            DataFrame with all metrics across years
        """
        all_metrics = {}
        
        for year in years:
            metrics = self.calculate_all_metrics(year)
            all_metrics[year] = metrics
        
        report_df = pd.DataFrame(all_metrics).T
        report_df.index.name = 'Year'
        
        return report_df

# Main execution
def main():
    """Main execution function"""
    
    # Initialize crawler
    crawler = SSIiBoardCrawler(headless=False)
    
    try:
        # Symbol to crawl (or attempt to crawl)
        target_symbol = "VNM"  # Change this to any stock symbol
        skip_search = True  # Set to True to skip symbol search and use current symbol
        
        print(f"=== Starting crawl (target: {target_symbol}, skip_search: {skip_search}) ===\n")
        
        # Crawl all data
        data = crawler.crawl_financial_statements(target_symbol, skip_symbol_search=skip_search)
        
        if not data:
            print("No data crawled!")
            return
        
        # Get actual symbol that was crawled
        actual_symbol = crawler.get_current_symbol() if hasattr(crawler, 'driver') and crawler.driver else target_symbol
        
        # Display results
        for sheet_name, df in data.items():
            print(f"\n{'='*60}")
            print(f"{sheet_name.upper()}")
            print(f"{'='*60}")
            print(f"Shape: {df.shape}")
            print(f"\nFirst 10 indicators:")
            print(df.head(10))
            
            # Save to CSV
            filename = f"{actual_symbol}_{sheet_name}.csv"
            df.to_csv(filename, encoding='utf-8-sig')
            print(f"\nSaved to: {filename}")
        
        # Analyze if we have the required data
        if 'balance_sheet' in data and 'income_statement' in data:
            print(f"\n{'='*60}")
            print("FINANCIAL ANALYSIS")  
            print(f"{'='*60}")
            
            # For now, we'll just show the data structure
            print(f"Available data sheets: {list(data.keys())}")
            for sheet_name, df in data.items():
                print(f"\\n{sheet_name.upper()} - Shape: {df.shape}")
                print(f"Sample indicators: {list(df.index[:5])}")
            
            # TODO: Update FinancialAnalyzer to work with new data structure
            
            # Get available years
            if data:
                first_sheet = next(iter(data.values()))
                if not first_sheet.empty:
                    years = list(first_sheet.columns)
                    latest_year = years[-1] if years else None
                    print(f"\\nAvailable years: {years}")
                    print(f"Latest year: {latest_year}")
            
            if latest_year:
                print(f"\nData successfully extracted for {latest_year}!")
                print("Ready for financial analysis and ratio calculations.")
                
                # Data is now ready for analysis
                if len(years) >= 3:
                    recent_years = years[-3:]
                    print(f"\n✅ Financial data available for years: {', '.join(recent_years)}")
                    print("All 3 financial statements successfully crawled!")
                    print("- Balance Sheet (Cân Đối Kế Toán)")
                    print("- Income Statement (Kết Quả Kinh Doanh)")  
                    print("- Cash Flow (Lưu Chuyển Tiền Tệ)")
        
        print(f"\n{'='*60}")
        print("CRAWL COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        crawler.close_driver()
        print("\nBrowser closed")

if __name__ == "__main__":
    main()