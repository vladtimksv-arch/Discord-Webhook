import os, requests
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

# 1. Чорний список (назви нормалізовано до нижнього регістру)
blacklisted_media = [
    "igromania", "dtf", "playground", "stopgame", "kanobu",
    "goha", "riot pixels", "gamemag", "ixbt", "shazoo",
    "3dnews", "cyber.sports.ru", "vk play", "gameguru", "zoneofgames"
]

feed_label = news.get('feedlabel', 'Невідоме джерело')
feed_name = news.get('feedname', '')

# Перевіряємо, чи є джерело в чорному списку
label_lower = feed_label.lower()
name_lower = feed_name.lower()

if any(media in label_lower or media in name_lower for media in blacklisted_media):
    print(f"Блокування: новина від російського ЗМІ ({feed_label}), ігноруємо.")
    exit()

# 2. Обробка та відправка (ТЕСТОВИЙ РЕЖИМ - БЕЗ ПЕРЕВІРКИ ЧАСУ)
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
    print("Успішно відправлено в Discord з тегом!")
else:
    print(f"Помилка відправки: {res.text}")
