import os, requests, time
import google.generativeai as genai

WEBHOOK_URL = os.environ["https://discord.com/api/webhooks/1549975886449872947/W7y2Kn0mGw0f4nbIZnGPM8KW8TLgwdgxPCklQfhcp8eXxRZcrRSr7rQZdmpdMCWhD2W3"]
genai.configure(api_key=os.environ["AQ.Ab8RN6J7oGuvR5Kk6bRrX8W163CLse60C1Im10tsF9qbRwsFmA"])
APP_ID = "1867240" # <-- ВПИШІТЬ ID ГРИ ТУТ

# 1. Отримання останньої новини
url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={APP_ID}&count=1"
response = requests.get(url)
news_items = response.json().get('appnews', {}).get('newsitems', [])

if not news_items:
    print("Новин не знайдено.")
    exit()

news = news_items[0]

# 2. Перевірка, чи новина свіжа (за останні 65 хвилин / 3900 секунд)
current_time = time.time()
if current_time - news['date'] < 3900:
    print(f"Знайдено нову новину: {news['title']}")
    
    # 3. Переклад через Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Переклади українською цей текст новини Steam. Зроби його читабельним, збережи основний зміст і всі оновлення до гри. Максимум 1900 символів (щоб влізло в Discord):\n\n{news['contents'][:4000]}"
    translation = model.generate_content(prompt).text
    
    # 4. Відправка в Discord
    data = {
        "content": f"**Новина: {news['title']}**\n\n{translation}\n\n*🔗 [Читати в Steam]({news['url']})*"
    }
    res = requests.post(WEBHOOK_URL, json=data)
    if res.status_code == 204:
        print("Успішно відправлено в Discord!")
    else:
        print(f"Помилка відправки: {res.text}")
else:
    print("Нових новин за останню годину немає. Чекаємо далі...")
