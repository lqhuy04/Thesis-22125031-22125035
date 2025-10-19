# -*- coding: utf-8 -*-
"""
Đăng nhập iBoard và trả về driver Selenium đã đăng nhập.
"""
import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://iboard.ssi.com.vn/"
WAIT_TIMEOUT = 15

def login_iboard():
    """Đăng nhập iBoard, trả về driver nếu thành công."""
    load_dotenv()
    USERNAME = os.getenv("IBOARD_USER")
    PASSWORD = os.getenv("IBOARD_PASS")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    driver.get(URL)

    try:
        # --- Click nút "Đăng nhập" ---
        btn_login_top = wait.until(EC.element_to_be_clickable((By.ID, "btnLogin")))
        btn_login_top.click()
        print("Đã click nút 'Đăng nhập'.")

        # --- Chờ iframe login ---
        iframe = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[contains(@src, 'accounts.ssi.com.vn/login')]")
            )
        )
        driver.switch_to.frame(iframe)
        print("✅ Đã chuyển vào iframe đăng nhập.")

        # --- Điền username / password ---
        username_input = wait.until(EC.visibility_of_element_located((By.ID, "txt-username")))
        password_input = wait.until(EC.visibility_of_element_located((By.ID, "txt-password")))

        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)

        # --- Bấm nút đăng nhập ---
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-login")))
        submit_btn.click()
        print("Đã bấm nút 'Đăng nhập' trong popup.")

        # --- Chờ xử lý xong ---
        time.sleep(3)
        driver.switch_to.default_content()
        print("✅ Đăng nhập thành công.")

        return driver

    except TimeoutException as e:
        print("❌ Lỗi khi đăng nhập:", e)
        driver.quit()
        raise
