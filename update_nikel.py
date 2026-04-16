import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def main():
    # 1. Cấu hình Selenium bám sát code của bạn
    options = Options()
    options.add_argument("--headless") # GitHub bắt buộc phải có headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Chống detect
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Đang truy cập Investing...")
        driver.get("https://vn.investing.com/commodities/nickel-historical-data")

        # Đợi table load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        rows = soup.select("table tbody tr")
        if not rows:
            print("Không tìm thấy dữ liệu bảng.")
            return

        # Lấy dòng đầu tiên (mới nhất)
        first_row = rows[0]
        cols = [c.text.strip() for c in first_row.find_all("td")]
        
        # Mapping dữ liệu theo đúng định dạng Sheet của bạn
        # cols[0]: Ngày, cols[1]: Lần cuối, cols[2]: Mở, cols[3]: Cao, cols[4]: Thấp, cols[5]: KL, cols[6]: %
        new_data = [cols[0], cols[1], cols[2], cols[3], cols[4], cols[5], cols[6]]
        print(f"Dữ liệu mới nhất: {new_data}")

        # 2. Đẩy vào Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Lấy file JSON key từ biến môi trường GitHub
        creds_raw = os.environ.get('G_SHEET_CONFIG')
        creds_dict = json.loads(creds_raw)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Mở Sheet (Thay tên chính xác của bạn vào đây)
        sheet = client.open("Tên Google Sheet của bạn").sheet1 

        # Kiểm tra trùng ngày
        existing_dates = sheet.col_values(1)
        if new_data[0] not in existing_dates:
            sheet.append_row(new_data)
            print("Cập nhật thành công!")
        else:
            print("Ngày này đã có dữ liệu, không ghi đè.")

    except Exception as e:
        print(f"Lỗi: {e}")
        if 'driver' in locals(): driver.quit()

if __name__ == "__main__":
    main()