import os, requests
from google import genai

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_KEY = os.environ["GEMINI_API_KEY"]
APP_ID = "1867240" # <-- ВПИШІТЬ ID ГРИ ТУТ

client = genai.Client(api_key=API_KEY)
url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={APP_ID}&count=1"
response = requests.get(url)
news_items = response.json().get('appnews', {}).get('newsitems', [])

if not news_items:
    print("Новин не знайдено.")
    exit()

news = news_items[0]
print(f"Обробка останньої новини: {news['title']}")

prompt = f"Переклади українською цей текст новини Steam. Зроби його читабельним, збережи основний зміст і оформи під повідомлення для Discord. Максимум 1900 символів:\n\n{news['contents'][:4000]}"

response = client.models.generate_content(
    model='gemini-1.5-flash',
    contents=prompt
)

data = {
    "content": f"**Новина: {news['title']}**\n\n{response.text}\n\n*🔗 [Читати в Steam]({news['url']})*"
}
res = requests.post(WEBHOOK_URL, json=data)

if res.status_code == 204:
    print("Успішно відправлено в Discord!")
else:
    print(f"Помилка відправки: {res.text}")
