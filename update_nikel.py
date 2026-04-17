import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def swap_number_format(value):
    if not value:
        return value
    return value.replace(",", "#").replace(".", ",").replace("#", ".")

def get_nickel_to_apps_script():
    options = Options()
    options.add_argument("--headless")  # Bật để chạy ổn định
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Thêm User-Agent để tránh bị Investing chặn ngay lập tức (Gây lỗi Timeout)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # 🔥 chống detect
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        driver.get("https://vn.investing.com/commodities/nickel-historical-data")

        # ✅ đợi table load (Tăng lên 20s vì Investing load khá chậm)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        rows = soup.select("table tbody tr")
        result = []

        for row in rows:
            cols = [c.text.strip() for c in row.find_all("td")]
            if len(cols) >= 6:
                change_val = cols[6] if len(cols) > 6 else ""
                clean_change = change_val.replace("+", "")
                result.append({
                    "date": cols[0],
                    "last": swap_number_format(cols[1]),
                    "open": swap_number_format(cols[2]),
                    "high": swap_number_format(cols[3]),
                    "low": swap_number_format(cols[4]),
                    "volume": cols[5],
                    "change": swap_number_format(clean_change)
                })

        # --- PHẦN TRUYỀN DỮ LIỆU VÀO APPS SCRIPT ---
        if result:
            result.reverse()
            print("Đã lấy được dữ liệu!")
            # Thay URL Web App của bạn vào đây
            APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyd7rfdh1YC2cC_RRSpqWqX3XYV4IFWUMdQUCmyViCmFjZEr-0B8PjsTvK72atmq2Zs/exec"
            
            # Truyền cả mảng result dưới dạng JSON
            response = requests.post(APPS_SCRIPT_URL, json={"data": result})
            return f"Đã gửi {len(result)} dòng. Apps Script phản hồi: {response.text}"
        else:
            return "Không lấy được dữ liệu."

    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return f"Lỗi: {str(e)}"

if __name__ == "__main__":
    print(get_nickel_to_apps_script())