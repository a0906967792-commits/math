import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime
import os
import json

import firebase_admin
from firebase_admin import credentials, firestore



# --- Firebase 初始化 (支援本地與 Vercel) ---
if os.path.exists('serviceAccountKey.json'):
    # 本地環境
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)


# --- 整合後的首頁 ---
@app.route("/")
def index():
    link = "<h1>歡迎來到鄭姿佳的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=姿佳&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST</a><hr>"
    link += "<a href=/math>計算次方與根號</a><hr>"
    link += "<br><a href=/read>讀取全部 Firestore 資料</a><br>"
    link += "<br><a href=/search>靜宜資管老師查詢(輸入關鍵字)</a><br>"
    link += "<hr><a href=/spider>網路爬蟲測試 (bs4)</a><br>"
    link += "<hr><a href=/movie1>爬取即將上映的電影</a><br>"
    link += "<br><a href=/spidermovie>爬取電影資料查詢</a><br>"

    return link


@app.route("/spidermovie", methods=["GET", "POST"])
def spidermovie():
    db = firestore.client()
    # 取得搜尋關鍵字 (來自表單的 q)
    q = request.args.get("q")
    
    # 基本的 HTML 搜尋表單
    R = """
    <form action="/spidermovie" method="get">
        請輸入片名關鍵字：<input type="text" name="q">
        <button type="submit">查詢</button>
    </form>
    <a href="/spidermovie">顯示全部電影</a>
    <hr>
    """

    # 從 Firebase 的 "電影2B" 集合抓取所有資料
    movies_ref = db.collection("電影2B")
    docs = movies_ref.get()
    
    found = False
    for doc in docs:
        movie = doc.to_dict()
        title = movie.get("title", "")
        
        # 篩選邏輯：如果沒輸入關鍵字則顯示全部；如果有輸入則比對片名
        if not q or q in title:
            found = True
            picture = movie.get("picture")
            hyperlink = movie.get("hyperlink")
            showDate = movie.get("showDate")
            
            # 組合顯示內容
            R += f'<a href="{hyperlink}" target="_blank"><b>{title}</b></a><br>'
            R += f'上映日期：{showDate}<br>'
            R += f'<img src="{picture}" width="150"><br><hr>'
            
    if not found:
        R += f"找不到包含「{q}」的電影。"

    R += "<br><a href='/'>回首頁</a>"
    return R



@app.route("/movie1")
def movie1():
    # 1. 取得使用者透過搜尋框輸入的關鍵字 (對應下面的 name="q")
    q = request.args.get("q")
    
    # 2. 建立網頁上方的搜尋表單 (HTML)
    # 這裡放一個輸入框和一個送出按鈕
    R = """
    <form action="/movie1" method="get">
        請輸入片名關鍵字：<input type="text" name="q">
        <button type="submit">查詢</button>
    </form>
    <a href="/movie1">顯示全部電影</a>
    <hr>
    """

    # 3. 爬蟲抓取資料
    url = "https://www.atmovies.com.tw/movie/next/#google_vignette"
    try:
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        found_any = False
        for item in result:
            try:
                movie_name = item.find("img").get("alt")
                
                # --- 篩選邏輯：如果沒輸入(None)或符合關鍵字就顯示 ---
                if q is None or q == "" or q in movie_name:
                    found_any = True
                    link_path = item.find("a").get("href")
                    img_path = item.find("img").get("src")
                    
                    full_link = "https://www.atmovies.com.tw" + link_path
                    full_img = "https://www.atmovies.com.tw" + img_path
                    
                    # 組合顯示內容：電影名(超連結) + 圖片
                    R += f'<a href="{full_link}" target="_blank"><b>{movie_name}</b></a><br>'
                    R += f'<img src="{full_img}" width="150"><br><br>'
            except:
                continue
        
        if q and not found_any:
            R += f"找不到關於「{q}」的電影。"

    except Exception as e:
        return f"連線錯誤: {str(e)}"

    return R




# --- 網路爬蟲測試 (bs4) ---
@app.route("/spider")
def spider():
    url = "https://www1.pu.edu.tw/~tcyang/course.html" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 修改重點：直接抓取網頁中所有的 <a> 標籤，以取得完整課程清單
        result = soup.find_all("a") 
        
        Result = "<h2>子青老師課程爬蟲結果</h2>"
        Result += "<table border='1'>"
        Result += "<tr><th width='200'>課程名稱</th><th>課程連結</th></tr>"
        
        for i in result:
            text = i.text.strip()
            href = i.get("href")
            
            # 過濾掉沒有連結、連結是返回(..)或是 JavaScript 的無效項目
            if href and "drive.google.com" in href: 
                Result += f"<tr><td>{text if text else '課程資料'}</td><td><a href='{href}' target='_blank'>{href}</a></td></tr>"
        
        Result += "</table>"
        
        return f"{Result}<br><a href='/'>返回首頁</a>"
        
    except Exception as e:
        return f"爬蟲發生錯誤：{str(e)}"

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        cond = request.form["keyword"]  # 取得你在輸入框打的字
        db = firestore.client()
        docs = db.collection("靜宜資管").get()
        
        Result = f"搜尋關鍵字「{cond}」的結果：<br><hr>"
        found = False
        
        for doc in docs:
            teacher = doc.to_dict()
            name = teacher.get("name", "")
            
            # 如果輸入的關鍵字在姓名裡面
            if cond in name:
                Result += f"找到老師：<b>{name}</b><br>"
                found = True
        
        if not found:
            Result += "查無此老師姓名。"
            
        return Result + "<br><a href='/search'>重新查詢</a> | <a href='/'>回首頁</a>"
    
    # GET 請求顯示搜尋頁面
    return render_template("search.html")

@app.route("/read")
def read():
    Result = "<h2>全部老師資料：</h2><hr>"
    db = firestore.client()
    docs = db.collection("靜宜資管").order_by("lab", direction=firestore.Query.DESCENDING).get()
    for doc in docs:
        Result += str(doc.to_dict()) + "<br>"
    return Result

# --- 其他功能路由 ---
@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    return render_template("2026b.html")

@app.route("/welcome", methods=["GET"])
def wlcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}"
    return render_template("account.html")

@app.route("/math")
def math_form():
    return render_template("math2.html")

@app.route("/math_result", methods=["POST"])
def math_result():
    try:
        x = float(request.form.get("x"))
        opt = request.form.get("opt")
        y = float(request.form.get("y"))

        if opt == "^":
            result = x ** y
            msg = f"{x} 的 {y} 次方 = {result}"
        elif opt == "√":
            if y == 0:
                msg = "錯誤：不能開 0 次方根"
            else:
                result = x ** (1/y)
                msg = f"{x} 的 {y} 次根號 = {result:.4f}"
        else:
            msg = "請選擇正確的運算符號"
            
    except Exception:
        msg = "請輸入有效的數字"

    return f"<h3>計算結果：{msg}</h3><br><a href='/math'>重新計算</a> | <a href='/'>回首頁</a>"

if __name__ == "__main__":
    app.run(debug=True)
