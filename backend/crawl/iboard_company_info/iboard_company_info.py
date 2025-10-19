# -*- coding: utf-8 -*-
"""
Sau khi đã đăng nhập, điều hướng tới phần 'Thông tin doanh nghiệp' → click 'TT cơ bản'.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

WAIT_TIMEOUT = 15

def get_iboard_company_info(driver):
    """Nhận driver đã đăng nhập, thao tác điều hướng tới tab TT cơ bản."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        # --- Mở menu "Thông tin thị trường" ---
        market_menu = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='menuitem' and @data-menu-id='mainMenu-marketInsight']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", market_menu)
        time.sleep(0.5)
        market_menu.click()
        print("✅ Đã mở menu 'Thông tin thị trường'.")

        # --- Click vào "Thông tin doanh nghiệp" ---
        company_info_btn = wait.until(EC.element_to_be_clickable((By.ID, "menu_companyProfile")))
        driver.execute_script("arguments[0].scrollIntoView(true);", company_info_btn)
        time.sleep(0.5)
        company_info_btn.click()
        print("✅ Đã click 'Thông tin doanh nghiệp'.")

        wait.until(EC.url_contains("/analysis/company-profile"))
        print("🌐 Trang 'Thông tin doanh nghiệp' đã được mở:", driver.current_url)

        # --- Click tab "Hồ sơ" ---
        profile_tab = wait.until(EC.element_to_be_clickable((By.ID, "tab_companyProfile")))
        driver.execute_script("arguments[0].scrollIntoView(true);", profile_tab)
        time.sleep(0.5)
        profile_tab.click()
        print("✅ Đã click tab 'Hồ sơ'.")

        # --- 🔹 Click nút "Giới thiệu" ---
        gioithieu_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Giới thiệu')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", gioithieu_btn)
        time.sleep(0.5)
        gioithieu_btn.click()
        print("✅ Đã click nút 'Giới thiệu'.")

        # --- Lấy nội dung phần "Giới thiệu" ---
        try:
            intro_paragraph = wait.until(
                EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Công ty Cổ phần Chứng khoán SSI')]"))
            )
            intro_text = intro_paragraph.text
            print("📄 Nội dung giới thiệu công ty:")
            print(intro_text)
        except TimeoutException:
            print("❌ Không tìm thấy đoạn giới thiệu công ty.")


        # --- Click nút "TT cơ bản" ---
        tt_coban_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'TT cơ bản')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", tt_coban_btn)
        time.sleep(0.5)
        tt_coban_btn.click()
        print("✅ Đã click nút 'TT cơ bản'.")

        # --- Lấy danh sách thông tin cơ bản của công ty ---
        try:
            # Đợi cho danh sách thông tin cơ bản hiển thị
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".company-basic-info")))

            company_info_divs = driver.find_elements(By.CSS_SELECTOR, ".company-basic-info")

            company_info = {}
            for div in company_info_divs:
                sub_divs = div.find_elements(By.CSS_SELECTOR, ".text-color-tertiary")
                if len(sub_divs) >= 2:
                    label = sub_divs[0].text.strip()
                    value = sub_divs[1].text.strip()
                    company_info[label] = value

            print("📋 Thông tin cơ bản của công ty:")
            for k, v in company_info.items():
                print(f"- {k}: {v}")

        except TimeoutException:
            print("❌ Không tìm thấy thông tin cơ bản của công ty.")

        # --- Lấy danh sách ban lãnh đạo ---
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".leader-group")))
            leader_groups = driver.find_elements(By.CSS_SELECTOR, ".leader-group")

            leaders = []
            for group in leader_groups:
                paragraphs = group.find_elements(By.TAG_NAME, "p")
                nameHtml = (paragraphs[0].get_attribute("outerHTML"))
                positionHtml = (paragraphs[1].get_attribute("outerHTML"))
                name = nameHtml.replace('<p class="text-color-tertiary">', '').replace('</p>', '')
                position = positionHtml.replace('<p class="text-color-cancel font-normal pt-1">', '').replace('</p>', '')
                leaders.append({"name": name, "position": position})

            print("📋 Danh sách ban lãnh đạo:")
            for leader in leaders:
                print(f"- {leader['name']}: {leader['position']}")

        except TimeoutException:
            print("❌ Không tìm thấy danh sách ban lãnh đạo.")

    except TimeoutException as e:
        print("❌ Lỗi khi điều hướng:", e)
