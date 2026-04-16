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
    return link

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
