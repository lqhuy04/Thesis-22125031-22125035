# -*- coding: utf-8 -*-
"""
File chính: gọi đăng nhập và sau đó lấy thông tin doanh nghiệp.
"""
from iboard_login import login_iboard
from iboard_company_info.iboard_company_info import get_iboard_company_info

if __name__ == "__main__":
    print("=== Bắt đầu quá trình tự động ===")

    # Bước 1: Đăng nhập
    driver = login_iboard()

    # Bước 2: Lấy thông tin doanh nghiệp
    get_iboard_company_info(driver)

    input("Nhấn Enter để đóng trình duyệt...")
    driver.quit()

    print("=== Hoàn thành ===")
