# --- scrape.py ---
# 這是我們的 Python 爬蟲腳本
# 它會抓取 API、排序資料、並儲存成 data.json

import requests
import json
import re
from datetime import datetime

# 1. 這是我們要抓取的 54 個法規 ID
LAW_IDS = [
    "FL022359", "FL016233", "FL016234", "FL054794", "FL060335", "FL016237",
    "FL015345", "FL015346", "FL064381", "FL063143", "FL068249", "FL015471",
    "FL015472", "FL015486", "FL015489", "FL015487", "FL025939", "FL015495",
    "FL015512", "FL015501", "FL015499", "GL004771", "GL007854", "GL005511",
    "GL005953", "GL007855", "FL015724", "FL026300", "FL015604", "FL015608",
    "GL007048", "FL015686", "GL006132", "FL020213", "FL042369", "FL021002",
    "FL020211", "GL007856", "GL006802", "FL015852", "FL015853", "FL015823",
    "FL015827", "GL007857", "GL006477", "FL015638", "GL007786", "FL015516",
    "FL015520", "GL007858", "FL015177", "FL015176", "GL007853", "FL015173"
]

# 2. 這是該網站的「秘密 API」網址
API_TEMPLATE_URL = "https://oaout.moenv.gov.tw/law/webapi/LawContent.ashx?id={id}&type=s"

# 3. 這是我們的「偽裝」 (假裝是 Chrome 瀏覽器)
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
}

# 4. 輔助功能：將民國日期字串轉為 Date 物件 (Python 版)
def convert_minguo_to_date(minguo_string):
    if not minguo_string or '年' not in minguo_string:
        return datetime(1970, 1, 1) # 回傳一個很早的日期
    
    parts = re.search(r'民國\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日', minguo_string)
    
    if parts:
        year = int(parts.group(1)) + 1911
        month = int(parts.group(2))
        day = int(parts.group(3))
        return datetime(year, month, day)
    
    return datetime(1970, 1, 1) # 解析失敗

# 5. 主要執行腳本
def main():
    print("開始抓取 54 筆法規資料...")
    law_data_list = []

    for index, law_id in enumerate(LAW_IDS):
        api_url = API_TEMPLATE_URL.format(id=law_id)
        
        try:
            # 帶著偽裝去抓取 API
            response = requests.get(api_url, headers=BROWSER_HEADERS, timeout=15)
            
            if response.status_code == 200:
                # 嘗試解析 JSON
                law_json = response.json()
                
                name = law_json.get("LawName") or "(未找到)"
                promulgation_date = law_json.get("PromulgationDate") or "N/A"
                amendment_date = law_json.get("AmendmentDate") or "N/A"
                
                # 為了排序，轉換日期
                date_to_sort = amendment_date if amendment_date != "N/A" else promulgation_date
                amendment_date_obj = convert_minguo_to_date(date_to_sort)
                
                law_data_list.append({
                    "id": law_id,
                    "name": name,
                    "promulgationDate": promulgation_date,
                    "amendmentDate": amendment_date,
                    "amendmentDateObj": amendment_date_obj # 排序用的
                })
                print(f"({index+1}/{len(LAW_IDS)}) 成功: {law_id} - {name}")

            else:
                print(f"({index+1}/{len(LAW_IDS)}) 失敗 (Code: {response.status_code}): {law_id}")
                law_data_list.append({ "id": law_id, "name": f"API抓取失敗 (Code: {response.status_code})", "promulgationDate": "N/A", "amendmentDate": "N/A", "amendmentDateObj": datetime(1970, 1, 1) })

        except Exception as e:
            # 包含 JSON 解析失敗 (伺服器回傳 HTML)
            print(f"({index+1}/{len(LAW_IDS)}) 失敗 (Exception: {e}): {law_id}")
            law_data_list.append({ "id": law_id, "name": "伺服器回傳了無效資料 (可能是 HTML)", "promulgationDate": "N/A", "amendmentDate": "N/A", "amendmentDateObj": datetime(1970, 1, 1) })

    print("資料抓取完畢，開始排序...")
    
    # 6. 依照「修正日期」排序 (日期最新的在最前面)
    law_data_list.sort(key=lambda x: x['amendmentDateObj'], reverse=True)
    
    # 7. 移除排序用的 'amendmentDateObj'，因為 JSON 不好儲存
    final_data_to_save = []
    for item in law_data_list:
        final_data_to_save.append({
            "id": item["id"],
            "name": item["name"],
            "promulgationDate": item["promulgationDate"],
            "amendmentDate": item["amendmentDate"]
        })

    # 8. 將最終結果寫入 data.json 檔案
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)

    print("成功建立 data.json 檔案！")

# 執行 main 函式
if __name__ == "__main__":
    main()
