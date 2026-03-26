def life(birthday_str):
    total = 0
    # 使用 for 迴圈遍歷字串中的每一個字元
    for digit in birthday_str:
        total += int(digit)  # 將字元轉回整數並累加
    
    print(f"您的西元生日8位數相加結果為：{total}")
    return total

# 1. 取得輸入（保持為字串，方便迴圈處理）
x = input("請輸入西元生日 8 位數 (例如 19950101): ")

# 檢查輸入長度是否正確（選填，增加程式魯棒性）
if len(x) == 8 and x.isdigit():
    # 2. 印出第一個數字（測試索引功能）
    print(f"生日的第一個數字是: {x[0]}")
    
    # 3. 執行函式
    life(x)
else:
    print("輸入格式錯誤，請輸入 8 位數字。")
