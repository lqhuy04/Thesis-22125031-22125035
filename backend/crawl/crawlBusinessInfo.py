# -*- coding: utf-8 -*-
"""
Script mở iBoard, click nút Đăng nhập, điền username/password và bấm Đăng nhập.
Comment bằng tiếng Việt.
"""
import os
from getpass import getpass
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# --- Cấu hình ---
URL = "https://iboard.ssi.com.vn/"
WAIT_TIMEOUT = 15  # giây

# --- Lấy thông tin đăng nhập ---
# đặt biến môi trường IBOARD_USER / IBOARD_PASS 
load_dotenv()

USERNAME = os.getenv("IBOARD_USER")
PASSWORD = os.getenv("IBOARD_PASS")

# --- Khởi tạo Chrome driver ---
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 15)
try:
    # Mở trang iBoard
    driver.get(URL)

    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    # --- Bước 1: Click nút "Đăng nhập" ở góc phải (id="btnLogin") ---
    try:
        btn_login_top = wait.until(EC.element_to_be_clickable((By.ID, "btnLogin")))
        btn_login_top.click()
        print("Đã click nút 'Đăng nhập' (top).")
    except TimeoutException:
        print("Không tìm thấy nút 'btnLogin' trong thời gian chờ.")
        raise

    # --- Bước 3: Chờ iframe popup hiển thị ---
    try:
        iframe = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[contains(@src, 'accounts.ssi.com.vn/login')]")
            )
        )
        print("✅ Popup iframe đã hiển thị.")
        print("🔹 src =", iframe.get_attribute("src"))
    except TimeoutException:
        print("❌ Không thấy iframe popup đăng nhập.")
        raise

    # --- Bước 4: Chuyển vào iframe để thao tác ---
    driver.switch_to.frame(iframe)
    print("🔄 Đã chuyển vào iframe đăng nhập.")

    # --- Bước 5: Chờ và điền username/password ---
    try:
        username_input = wait.until(EC.visibility_of_element_located((By.ID, "txt-username")))
        password_input = wait.until(EC.visibility_of_element_located((By.ID, "txt-password")))
        print("✅ Tìm thấy các ô username/password.")
    except TimeoutException:
        print("❌ Không thấy các ô username/password trong iframe.")
        raise

    # --- Bước 3: Điền thông tin ---
    username_input.clear()
    username_input.send_keys(USERNAME)
    password_input.clear()
    password_input.send_keys(PASSWORD)
    print("Đã điền username và password.")

    # --- Bước 4: Click nút "Đăng nhập" trong popup ---
    # Button có class="btn-login" và type="submit"
    try:
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-login")))
        submit_btn.click()
        print("Đã click nút 'Đăng nhập' trong popup.")
    except TimeoutException:
        print("Không tìm thấy nút submit trong popup.")
        raise

    # --- Bước 5: Chờ kết quả (ví dụ: chờ phần tử hiển thị sau khi login) ---
    # Ở đây mình chờ 1 phần tử đại diện sau khi login, bạn có thể thay bằng selector phù hợp.
    # Ví dụ chờ nút "Đặt lệnh" (nếu có) hoặc kiểm tra thay đổi tiêu đề/người dùng hiển thị.
    try:
        # Thay selector sau đây nếu bạn muốn kiểm tra 1 phần tử cụ thể sau khi login
        # wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "selector_sau_khi_login")))
        # Tạm thời mình đợi 3 giây để hệ thống xử lý
        time.sleep(3)
        print("Hoàn thành thao tác đăng nhập (đã gửi form).")
    except Exception:
        pass


    # --- Bước 6: Quay lại frame chính ---
    driver.switch_to.default_content()
    print("🔙 Đã quay về frame chính.")

    # --- Bước 7: Mở menu "Thông tin thị trường" ---
    try:
        market_menu = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@role='menuitem' and @data-menu-id='mainMenu-marketInsight']"
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", market_menu)
        time.sleep(0.5)
        market_menu.click()
        print("✅ Đã mở menu 'Thông tin thị trường'.")
    except TimeoutException:
        print("❌ Không tìm thấy menu 'Thông tin thị trường'.")
        raise

    # --- Bước 8: Click vào 'Thông tin doanh nghiệp' ---
    try:
        company_info_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "menu_companyProfile"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", company_info_btn)
        time.sleep(0.5)
        company_info_btn.click()
        print("✅ Đã click vào menu 'Thông tin doanh nghiệp'.")

        # Xác nhận trang đã mở
        wait.until(EC.url_contains("/analysis/company-profile"))
        print("🌐 Trang 'Thông tin doanh nghiệp' đã được mở:", driver.current_url)

    except TimeoutException:
        print("❌ Không tìm thấy mục 'Thông tin doanh nghiệp' sau khi mở menu.")

    # --- Bước 9: Click vào tab "Hồ sơ" ---
    try:
        profile_tab = wait.until(
            EC.element_to_be_clickable((By.ID, "tab_companyProfile"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", profile_tab)
        time.sleep(0.5)
        profile_tab.click()
        print("✅ Đã click vào tab 'Hồ sơ'.")

        # (Tuỳ chọn) chờ phần nội dung của tab này tải ra, ví dụ:
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Hồ sơ doanh nghiệp')]"))
        )
        print("📄 Nội dung 'Hồ sơ doanh nghiệp' đã tải thành công.")

    except TimeoutException:
        print("❌ Không thể click vào tab 'Hồ sơ'. Có thể trang chưa tải xong hoặc ID thay đổi.")



    # Giữ trình duyệt mở để bạn kiểm tra
    input("Nhấn Enter để đóng trình duyệt...")

except Exception as e:
    print("Có lỗi xảy ra:", e)

finally:
    driver.quit()
