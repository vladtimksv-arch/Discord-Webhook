import os, requests, time
from google import genai

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_KEY = os.environ["GEMINI_API_KEY"]
APP_ID = "1867240"

client = genai.Client(api_key=API_KEY)
url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={APP_ID}&count=1"
response = requests.get(url)
news_items = response.json().get('appnews', {}).get('newsitems', [])

if not news_items:
    print("Новин не знайдено.")
    exit()

news = news_items[0]
current_time = time.time()
feed_label = news.get('feedlabel', 'Невідоме джерело')

# Замініть 1200 на 9999999, щоб протестувати генерацію тегів прямо зараз, а потім поверніть назад!
if current_time - news['date'] < 1200:
    print(f"Обробка новини від {feed_label}: {news['title']}")
    
    prompt = f"""Проаналізуй текст новини (Джерело: {feed_label}) та переклади його українською.
    
1. На самому початку повідомлення обов'язково встав один із цих тегів, який найбільше підходить за змістом:
**[ 🛠 ПАТЧНОУТ ]** — виправлення багів, технічні оновлення гри.
**[ 📢 НОВИНИ СТУДІЇ ]** — офіційні анонси, події від розробників.
**[ 📰 МЕДІА / СТАТТІ ]** — статті, огляди, інтерв'ю від ігрових журналістів.
**[ 🟡 ЧУТКИ ]** — непідтверджена інформація.
**[ 🎉 ІВЕНТ ]** — знижки, розпродажі.

2. З нового рядка напиши заголовок новини жирним шрифтом: **{news['title']}**
3. Далі напиши читабельний переклад тексту. Не вставляй прямі посилання на зображення. Максимум 1800 символів.

Текст: {news['contents'][:4000]}"""
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    
    safe_url = news['url'].replace(" ", "%20")
    
    data = {
        "content": f"{response.text}\n\nОригінал: {safe_url}"
    }
    res = requests.post(WEBHOOK_URL, json=data)
    
    if res.status_code == 204:
        print("Успішно відправлено в Discord з новим тегом!")
    else:
        print(f"Помилка відправки: {res.text}")
else:
    print("Нових новин за останні 20 хвилин немає. Чекаємо далі...")
