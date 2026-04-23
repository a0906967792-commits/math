import requests
from bs4 import BeautifulSoup

url = "https://www.atmovies.com.tw/movie/next/#google_vignette"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")
result = sp.select(".filmListAllX li")

q = input("請輸入片名關鍵字：")

for item in result:
    # 取得電影名稱
    movie_name = item.find("img").get("alt")
    
    # 檢查關鍵字是否在電影名稱中
    if q in movie_name:
        # --- 重點：下面這幾行一定要縮排 (打一個 Tab 鍵) ---
        print(movie_name)
        print("https://www.atmovies.com.tw/" + item.find("a").get("href"))
        print("https://www.atmovies.com.tw/" + item.find("img").get("src"))
        print()