from google import genai

import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request, make_response, jsonify
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

# 在全域（函式外面）建立 Client 物件，只初始化一次即可，不用每次初始化
client = genai.Client()



# --- 整合後的首頁 ---
@app.route("/")
def index():
    link = "<h1>歡迎來到鄭姿佳的網站20260528</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=姿佳&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST</a><hr>"
    link += "<a href=/math>計算次方與根號</a><hr>"
    link += "<br><a href=/read>讀取全部 Firestore 資料</a><hr>"
    link += "<br><a href=/search>靜宜資管老師查詢(輸入關鍵字)</a>"
    link += "<hr><a href=/spider>網路爬蟲測試 (bs4)</a>"
    link += "<hr><a href=/movie1>爬取即將上映的電影</a><hr>"
    link += "<br><a href=/spidermovie>爬取電影資料查詢</a><hr>"
    link += "<br><a href=/road>台中市十大肇事路口</a><hr>"
    link += "<br><a href=/road1>台中市十大肇事路口查詢</a><hr>"
    link += "<br><a href=/weather>天氣</a><hr>"
    link += "<br><a href=/rate>本週新片進DB</a><hr>"
    link += "<br><a href=/wd>聊天機器人</a><hr>"
    link += "<br><a href=/AI>ai</a><hr>"

    return link

@app.route("/AI")
def AI():
    # 每次使用者拜訪該路徑時，直接使用全域的 client 呼叫模型
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents='我想查詢靜宜大學資管系的評價？',
    )
    
    # 回傳生成的文字
    return response.text

@app.route("/wd")
def wd():
    return render_template("wd.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action = req["queryResult"]["action"]
   
    if action == "rateChoice":
        rate = req["queryResult"]["parameters"]["rate"]
       
        db = firestore.client()
        collection_ref = db.collection("本週新片含分級")
        docs = collection_ref.where("rate", "==", rate).get()
       
        res = f"為您找出的本週 {rate} 電影有：\n"
        found = False
        for doc in docs:
            found = True
            m = doc.to_dict()
            res += f"- {m.get('title')} (片長：{m.get('showLength')} 分)\n"
       
        if not found:
            res = f"抱歉，本週資料庫中沒有標記為 {rate} 的電影喔！"
           
        return make_response(jsonify({"fulfillmentText": res}))

    return make_response(jsonify({"fulfillmentText": "Webhook 運作正常，但未觸發特定動作。"}))


#------本周新片-------
@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate


#天氣
@app.route("/weather")
def weather():
    import requests, json
    from flask import request
    
    city = request.args.get("city", "臺中市")
    city = city.replace("台", "臺")
    
    # ⚠️ 請確認這裡的 Token 是你從氣象署官網申請的個人授權碼
    token = "rdec-key-123-45678-011121314" 
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
    
    R = f"<h1>{city} 天氣查詢結果</h1><br>"
    
    try:
        response = requests.get(url, timeout=10)
        # 檢查 HTTP 狀態碼是否為 200 (成功)
        if response.status_code == 200:
            json_data = response.json() # 直接使用 .json() 比較安全
            
            if "records" in json_data and json_data["records"]["location"]:
                location_data = json_data["records"]["location"]
                weather_element = location_data[0]["weatherElement"]
                state = weather_element[0]["time"][0]["parameter"]["parameterName"]
                rain = weather_element[1]["time"][0]["parameter"]["parameterName"]
                
                R += f"目前天氣：<b>{state}</b><br>"
                R += f"降雨機率：<b>{rain}%</b><br>"
            else:
                R += "找不到該縣市資料，請輸入正確名稱（如：臺中市）。<br>"
        else:
            R += f"API 連線失敗，狀態碼：{response.status_code} (請檢查 Token 是否正確)<br>"
            
    except Exception as e:
        R += f"查詢發生錯誤：{str(e)}<br>"

    R += "<br><hr><a href='/'>回首頁</a>"
    return R


#十大肇事路口查詢版
@app.route("/road1", methods=["GET", "POST"])
def road1():
    q = request.values.get("q")
    results = ""
   
    if q:
        url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
       
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://datacenter.taichung.gov.tw/',
            'X-Requested-With': 'XMLHttpRequest'
        }
       
        max_retries = 3  # 最多重試 3 次
        for i in range(max_retries):
            try:
                # verify=False 跳過 SSL 檢查，有時能解決斷連問題
                # 使用 requests 直接連線
                response = requests.get(url, headers=headers, timeout=15, verify=False)
                response.encoding = 'utf-8'
               
                if response.status_code == 200:
                    json_data = response.json()
                    found = False
                    results = "<h3>查詢結果：</h3><table border='1' style='border-collapse: collapse; width:100%;'>"
                    results += "<tr style='background-color:#e6f3ff;'><th>路口名稱</th><th>件數</th><th>主要肇因</th></tr>"
                   
                    for item in json_data:
                        if q in item.get("路口名稱", ""):
                            found = True
                            results += f"<tr><td>{item['路口名稱']}</td><td>{item['總件數']}</td><td>{item['主要肇因']}</td></tr>"
                    results += "</table>"
                   
                    if not found:
                        results = f"<p style='color:orange;'>查無關於「{q}」的資料。</p>"
                    break # 成功抓到資料，跳出重試迴圈
               
            except Exception as e:
                if i < max_retries - 1:
                    time.sleep(1) # 失敗後等一秒再試
                    continue
                else:
                    results = f"<div style='color:red;'>連線失敗第 {i+1} 次：{str(e)}<br>目前政府伺服器拒絕您的 IP 連線，建議換個網路試試看。</div>"

    html = f"""
    <h1>台中市易肇事路口查詢</h1>
    <form action="/road" method="get">
        請輸入路名：<input type="text" name="q" value="{q if q else ''}">
        <button type="submit">查詢</button>
    </form>
    <hr>
    {results}
    <br><a href="/">返回首頁</a>
    """
    return html


#十字路口沒查詢
@app.route("/road", methods=["GET", "POST"])
def road():
    # 建立網頁標題與基礎 HTML
    R = "<h1>十大肇事路口(113年10月)作者:姿佳</h1><br>"
    
    import requests, json
    import urllib3
    from flask import request

    # 隱藏 SSL 安全警告（因為我們會使用 verify=False）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    
    # 模擬更完整的瀏覽器標頭
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        # verify=False 解決憑證問題, timeout=10 防止卡死
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.encoding = 'utf-8' # 確保中文不變亂碼
        
        # 轉換 JSON
        JsonData = response.json()
        
        # 從網址取得 q 參數，例如：/road?q=中科路
        Road_query = request.args.get("q", "") 

        found = False
        for item in JsonData:
            # 判斷路口名稱是否包含搜尋關鍵字
            if Road_query in item.get("路口名稱", ""):
                # 注意：這裡使用 f-string 時，item['路口名稱'] 要用單引號，外面用雙引號
                R += f"<b>{item['路口名稱']}</b>，原因：{item['主要肇因']} <br>"
                found = True
        
        if not found:
            if Road_query == "":
                R += "<i>請在網址後加上 ?q=路名 來搜尋，或查看下方所有列表：</i><br><br>"
                # 如果沒搜關鍵字，也可以考慮顯示前幾筆或全部
                for item in JsonData[:10]: # 先顯示前10筆示範
                    R += f"{item['路口名稱']} <br>"
            else:
                R += f"抱歉，查無關於「{Road_query}」的相關資料！<br>"
    except Exception as e:
        R += f"<div style='color:red;'>連線錯誤：{str(e)}</div>"

    R += "<br><hr><a href='/'>回首頁</a>"
    return R



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
