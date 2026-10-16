"""
Job hằng ngày: lấy dữ liệu Niken 30 ngày gần nhất từ Investing và gửi vào Apps Script.
Thay cho bản Selenium cũ (bị Investing chặn Chrome headless từ khoảng 18/06/2026).

Cần: pip install curl_cffi requests
"""
import json
from datetime import datetime, date, timedelta

import requests
from curl_cffi import requests as creq

INSTRUMENT_ID = "959208"  # Hợp đồng Tương lai Niken (NICKELc1)
DAYS_BACK = 30
PAGE_URL = "https://vn.investing.com/commodities/nickel-historical-data"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFDlZtv3aA0wFwvpR8dX6YoaA-Pd0Z8XXl6GN_V4ZocLwApPlpn4wTwsNR-uiSfGzNYw/exec"
PROFILES = ("chrome124", "chrome", "safari17_0", "edge101")


def swap_number_format(value):
    if not value:
        return value
    return value.replace(",", "#").replace(".", ",").replace("#", ".")


def to_row(item):
    d = datetime.fromisoformat(str(item["rowDateTimestamp"]).replace("Z", "+00:00"))
    chg = item.get("change_precentRaw")
    change = f"{float(chg):.2f}%" if chg not in (None, "") else str(item.get("change_precent", "")).replace("+", "")
    return {
        "date": d.strftime("%d/%m/%Y"),
        "last": swap_number_format(item.get("last_close", "")),
        "open": swap_number_format(item.get("last_open", "")),
        "high": swap_number_format(item.get("last_max", "")),
        "low": swap_number_format(item.get("last_min", "")),
        "volume": str(item.get("volume", "") or ""),
        "change": swap_number_format(change),
    }


def fetch(start, end):
    url = (
        f"https://api.investing.com/api/financialdata/historical/{INSTRUMENT_ID}"
        f"?start-date={start}&end-date={end}&time-frame=Daily&add-missing-rows=false"
    )
    headers = {
        "domain-id": "vn",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://vn.investing.com",
        "Referer": PAGE_URL,
    }
    errors = []
    for profile in PROFILES:
        try:
            r = creq.get(url, headers=headers, impersonate=profile, timeout=30)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                return json.loads(r.text).get("data") or []
            errors.append(f"{profile}: HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"{profile}: {e}")
    raise RuntimeError("Không gọi được API -> " + " | ".join(errors))


def get_nickel_to_apps_script():
    try:
        end = date.today()
        start = end - timedelta(days=DAYS_BACK)
        items = fetch(start.isoformat(), end.isoformat())
        if not items:
            return "Không lấy được dữ liệu."
        result = [to_row(it) for it in items]
        result.sort(key=lambda r: datetime.strptime(r["date"], "%d/%m/%Y"))  # cũ -> mới
        print(f"Đã lấy được dữ liệu! {result[0]['date']} -> {result[-1]['date']}")
        response = requests.post(APPS_SCRIPT_URL, json={"data": result}, timeout=120)
        return f"Đã gửi {len(result)} dòng. Apps Script phản hồi: {response.text}"
    except Exception as e:
        return f"Lỗi: {e}"


if __name__ == "__main__":
    print(get_nickel_to_apps_script())