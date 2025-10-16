"""
SSI iBoard Company Profile Scraper - Fixed Version
Compatible with Python 3.12.7
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import sys

class SSICompanyProfileScraper:
    def __init__(self, headless=False):
        """Initialize the scraper"""
        print("🔧 Initializing browser...")
        
        try:
            # Setup Chrome options
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Automatically download and use correct ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            
            print("✅ Browser initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing browser: {e}")
            print("\nPress Enter to exit...")
            input()
            sys.exit(1)
        
    def get_stock_price_info(self):
        """Extract stock price information"""
        try:
            print("📊 Extracting price information...")
            data = {}
            
            # Wait for price element to be visible
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='stock-header-price']")
            ))
            
            # Current price
            try:
                data['current_price'] = self.driver.find_element(
                    By.XPATH, "//div[@class='stock-header-price']//div[@class='price']"
                ).text
            except:
                data['current_price'] = "N/A"
            
            # Price change
            try:
                data['price_change'] = self.driver.find_element(
                    By.XPATH, "//div[@class='price-change']"
                ).text
            except:
                data['price_change'] = "N/A"
            
            # Total volume
            try:
                data['total_volume'] = self.driver.find_element(
                    By.XPATH, "//div[contains(text(), 'TỔNG KL:')]/following-sibling::div"
                ).text
            except:
                data['total_volume'] = "N/A"
            
            print("✅ Price information extracted")
            return data
            
        except Exception as e:
            print(f"⚠️ Error getting price info: {e}")
            return {'error': str(e)}
    
    def get_company_info(self):
        """Extract company profile information"""
        try:
            print("🏢 Extracting company information...")
            data = {}
            
            # Company name
            try:
                data['company_name'] = self.driver.find_element(
                    By.XPATH, "//div[@id='stock-detail-header']//div[@class='flex-none font-bold pt-1']"
                ).text
            except:
                data['company_name'] = "N/A"
            
            # Switch to company profile tab if not active
            try:
                profile_tab = self.driver.find_element(By.XPATH, "//li[@id='tab_companyProfile']")
                if 'active' not in profile_tab.get_attribute('class'):
                    profile_tab.click()
                    time.sleep(2)
            except:
                pass
            
            # Company overview
            try:
                overview_xpath = "//div[@class='company-over-view text-color-tertiary']//p"
                overview_elements = self.driver.find_elements(By.XPATH, overview_xpath)
                data['overview'] = ' '.join([elem.text for elem in overview_elements if elem.text])
            except:
                data['overview'] = "N/A"
            
            print("✅ Company information extracted")
            return data
            
        except Exception as e:
            print(f"⚠️ Error getting company info: {e}")
            return {'error': str(e)}
    
    def get_subsidiaries(self):
        """Extract subsidiary companies information"""
        try:
            print("🏭 Extracting subsidiaries information...")
            subsidiaries = []
            
            # Click on subsidiaries tab
            try:
                sub_tab = self.driver.find_element(
                    By.XPATH, "//button[@id='headlessui-tabs-tab-15']"
                )
                if 'selected' not in sub_tab.get_attribute('aria-selected'):
                    sub_tab.click()
                    time.sleep(2)
            except:
                pass
            
            # Get all subsidiary rows
            try:
                rows = self.driver.find_elements(
                    By.XPATH, "//div[@id='sub-company']//tbody/tr"
                )
                
                for row in rows:
                    try:
                        tds = row.find_elements(By.XPATH, ".//td")
                        if len(tds) >= 4:
                            sub_data = {
                                'name': tds[0].text,
                                'symbol': tds[1].text,
                                'capital': tds[2].text,
                                'ownership': tds[3].text
                            }
                            subsidiaries.append(sub_data)
                    except:
                        continue
            except:
                pass
            
            print(f"✅ Found {len(subsidiaries)} subsidiaries")
            return subsidiaries
            
        except Exception as e:
            print(f"⚠️ Error getting subsidiaries: {e}")
            return []
    
    def get_leadership(self):
        """Extract leadership information"""
        try:
            print("👔 Extracting leadership information...")
            leaders = []
            
            # Click on leadership tab
            try:
                leader_tab = self.driver.find_element(
                    By.XPATH, "//button[@id='headlessui-tabs-tab-18']"
                )
                if 'selected' not in leader_tab.get_attribute('aria-selected'):
                    leader_tab.click()
                    time.sleep(2)
            except:
                pass
            
            # Get all leader groups
            try:
                leader_groups = self.driver.find_elements(
                    By.XPATH, "//div[@class='leader-group']"
                )
                
                for group in leader_groups:
                    try:
                        ps = group.find_elements(By.XPATH, ".//p")
                        if len(ps) >= 2:
                            leader_data = {
                                'name': ps[0].text,
                                'position': ps[1].text
                            }
                            leaders.append(leader_data)
                    except:
                        continue
            except:
                pass
            
            print(f"✅ Found {len(leaders)} leaders")
            return leaders
            
        except Exception as e:
            print(f"⚠️ Error getting leadership: {e}")
            return []
    
    def scrape_company(self, symbol='VNM'):
        """Main scraping function"""
        try:
            url = "https://iboard.ssi.com.vn/analysis/company-profile"
            print(f"\n🌐 Navigating to {url}")
            self.driver.get(url)
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(10)
            
            # Collect all data
            print("\n" + "="*50)
            print("Starting data collection...")
            print("="*50)
            
            company_data = {
                'symbol': symbol,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'price_info': self.get_stock_price_info(),
                'company_info': self.get_company_info(),
                'subsidiaries': self.get_subsidiaries(),
                'leadership': self.get_leadership()
            }
            
            return company_data
            
        except Exception as e:
            print(f"❌ Error scraping company: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
            print("✅ Browser closed")
        except:
            pass

    def login(self, username: str, password: str):
        """Automate login to SSI iBoard"""
        print("🔐 Logging in to SSI iBoard...")
        self.driver.get("https://iboard.ssi.com.vn/auth/login")

        try:
            # Click the first "Đăng nhập" button to redirect to SSO login page
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnToLoginSSO"))
            )
            login_button.click()
            print("➡️ Redirecting to SSO login page...")

            # Wait for username field on SSO page
            self.wait.until(EC.presence_of_element_located((By.ID, "txt-username")))

            # Fill in username and password
            username_field = self.driver.find_element(By.ID, "txt-username")
            password_field = self.driver.find_element(By.ID, "txt-password")

            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            # Click submit button
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login")
            submit_btn.click()
            print("✅ Submitted login form")

            # Wait until redirected back to iboard (authenticated)
            self.wait.until(
                EC.url_contains("https://iboard.ssi.com.vn")
            )
            print("🎉 Login successful!")

        except Exception as e:
            print(f"❌ Login failed: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("login_error.png")
            raise


# Main execution
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("SSI Company Profile Scraper")
        print("Python Version:", sys.version)
        print("=" * 60)
        
        # Set headless=False to see the browser in action
        # Set headless=True to run in background
        print("\n🚀 Starting scraper...")
        scraper = SSICompanyProfileScraper(headless=False)

        scraper.login("0936867778", "!Aabb1122")
        
        print("\n🔍 Starting to scrape SSI company data...")
        print("Please wait, this may take 15-30 seconds...\n")
        
        # Scrape SSI company data
        data = scraper.scrape_company('SSI')
        
        if data:
            print("\n" + "="*60)
            print("✅ Data scraped successfully!")
            print("="*60)
            
            # Print some key information
            print("\n📊 Price Information:")
            print(f"   Current Price: {data['price_info'].get('current_price', 'N/A')}")
            print(f"   Price Change: {data['price_info'].get('price_change', 'N/A')}")
            print(f"   Total Volume: {data['price_info'].get('total_volume', 'N/A')}")
            
            print("\n🏢 Company Information:")
            print(f"   Name: {data['company_info'].get('company_name', 'N/A')}")
            
            overview = data['company_info'].get('overview', 'N/A')
            if len(overview) > 200:
                print(f"   Overview: {overview[:200]}...")
            else:
                print(f"   Overview: {overview}")
            
            print(f"\n👔 Leadership Team: {len(data.get('leadership', []))} members")
            print(f"🏭 Subsidiaries: {len(data.get('subsidiaries', []))} companies")
            
            # Save to file
            filename = 'ssi_company_data.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Full data saved to: {filename}")
            print("\n" + "="*60)
            print("✅ Scraping completed successfully!")
            print("="*60)
        else:
            print("\n❌ Failed to scrape data")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            print("\n🔒 Closing browser...")
            scraper.close()
        except:
            pass
        
        print("\n✅ Done!")
        print("\nPress Enter to exit...")
        input()  # This keeps the window open