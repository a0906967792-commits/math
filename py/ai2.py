from google import genai

client = genai.Client(api_key='AIzaSyA9QzO3rZPeai6OOv4LkdBiwXWnlo9U8P4')

question = input("請輸入您要問AI的問題?")

# 直接體驗最新一代的 3.5 Flash 
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=question,
)

print(response.text)
