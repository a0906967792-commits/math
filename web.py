from flask import Flask,render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
   link =  "<h1>歡迎來到鄭姿佳的網站20260409</h1>"
   link +=  "<a href=/mis>課程</a><hr>"
   link +=  "<a href=/today>現在日期時間</a><hr>"
   link +=  "<a href=/me>關於我</a><hr>"
   link +=  "<a href=/welcome?u=姿佳&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
   link +=  "<a href=/account>POST</a><hr>"
   link += "<a href=/math>計算次方與根號</a><hr>"
   link += "<br><a href=/read>讀取Firestore資料</a><br>"
   return link

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")
    
    # 這裡將排序後的結果存入 docs，並刪除原本重複的 docs = collection_ref.get()
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get()  
    
    for doc in docs:          
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html",datetime = str(now))

@app.route("/me")
def me():
    return render_template("2026b.html",)

@app.route("/welcome",methods=["GET"])
def wlcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html",name= user, dep = d,course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math")
def math_form():
    return render_template("math2.html")

@app.route("/math_result", methods=["POST"])
def math_result():
    # 取得表單傳過來的數值
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
            
    except Exception as e:
        msg = "請輸入有效的數字"

    return f"<h3>計算結果：{msg}</h3><br><a href='/math'>重新計算</a> | <a href='/'>回首頁</a>"




if __name__ == "__main__":
    app.run(debug=True)
