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

# 1. Чорний список (російські ЗМІ)
blacklisted_media = [
    "igromania", "dtf", "playground", "stopgame", "kanobu",
    "goha", "riot pixels", "gamemag", "ixbt", "shazoo",
    "3dnews", "cyber.sports.ru", "vk play", "gameguru", "zoneofgames"
]

feed_label = news.get('feedlabel', 'Невідоме джерело')
feed_name = news.get('feedname', '')

if any(media in feed_label.lower() or media in feed_name.lower() for media in blacklisted_media):
    print(f"Блокування: новина від російського ЗМІ ({feed_label}), ігноруємо.")
    exit()

print(f"Обробка новини від {feed_label}: {news['title']}")

# 2. Промпт із хештегами для зручного пошуку
prompt = f"""Проаналізуй текст новини (Джерело: {feed_label}) та переклади його українською.

1. На самому початку повідомлення обов'язково встав один із цих хештегів (разом з емодзі), який найбільше підходить за змістом:
#Патчноут 🛠 — виправлення багів, технічні оновлення гри.
#Новини_Студії 📢 — офіційні анонси, події від розробників.
#Стаття 📰 — статті, огляди, інтерв'ю від ігрових журналістів.
#Чутки 🟡 — непідтверджена інформація.
#Івент 🎉 — знижки, розпродажі, події.

2. З нового рядка напиши заголовок новини жирним шрифтом: **{news['title']}**
3. Далі напиши читабельний переклад тексту. Не вставляй прямі посилання на зображення. Максимум 1800 символів.

Текст: {news['contents'][:4000]}"""

max_retries = 3
response_text = ""

for attempt in range(max_retries):
    try:
        gen_response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt
        )
        response_text = gen_response.text
        break 
    except Exception as e:
        if '503' in str(e) and attempt < max_retries - 1:
            print(f"Сервери Google перевантажені (503). Чекаємо 15 секунд... (Спроба {attempt + 1}/{max_retries})")
            time.sleep(15)
        else:
            print(f"Помилка генерації тексту: {e}")
            exit()

# 3. Відправка в Discord
safe_url = news['url'].replace(" ", "%20")

data = {
    "content": f"{response_text}\n\nОригінал: {safe_url}"
}
res = requests.post(WEBHOOK_URL, json=data)

if res.status_code == 204:
    print("Успішно відправлено в Discord з хештегом!")
else:
    print(f"Помилка відправки в Discord: {res.text}")
