import os, requests, time
from google import genai

# 1. Завантаження ключів безпечно із секретів GitHub
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_KEY = os.environ["GEMINI_API_KEY"]
APP_ID = "1867240" # ID гри Wardogs

# 2. Отримання новин зі Steam API
client = genai.Client(api_key=API_KEY)
url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={APP_ID}&count=1"
response = requests.get(url)
news_items = response.json().get('appnews', {}).get('newsitems', [])

if not news_items:
    print("Новин не знайдено.")
    exit()

news = news_items[0]
current_time = time.time()

# 3. Перевірка на свіжість (1200 секунд = 20 хвилин). 
# Якщо новина старша, скрипт зупиняється, щоб не дублювати сповіщення.
if current_time - news['date'] > 1200:
    print("Нових новин за останні 20 хвилин немає. Чекаємо далі...")
    exit()

# 4. Чорний список (російські медіа — блокуємо суворо)
blacklisted_media = [
    "igromania", "dtf", "playground", "stopgame", "kanobu",
    "goha", "riot pixels", "gamemag", "ixbt", "shazoo",
    "3dnews", "cyber.sports.ru", "vk play", "gameguru", "zoneofgames"
]

feed_label = news.get('feedlabel', 'Офіційне джерело')
feed_name = news.get('feedname', '')

if any(media in feed_label.lower() or media in feed_name.lower() for media in blacklisted_media):
    print(f"Блокування: новина від російського ЗМІ ({feed_label}), ігноруємо.")
    exit()

print(f"Обробка свіжої новини від джерела: {feed_label}")

# 5. Промпт для Gemini з вимогою розмістити категорію в кінець
prompt = f"""Проаналізуй текст новини (Джерело: {feed_label}) та переклади його українською.

1. Зроби заголовок новини жирним шрифтом на самому початку: **{news['title']}**
2. Напиши читабельний переклад тексту. Не вставляй прямі посилання на зображення. Максимум 1800 символів.
3. В самому кінці перекладу додай один із цих тегів категорії (вибери найбільш підходящий):
• Категорія: 🛠 Патчноут (для технічних оновлень, виправлення багів)
• Категорія: 📢 Новини студії (для офіційних анонсів від розробників)
• Категорія: 📰 Медіа та статті (для матеріалів від IGN, PC Gamer, Eurogamer, Rock Paper Shotgun та інших світових ЗМІ)
• Категорія: 🟡 Чутки
• Категорія: 🎉 Івент

Текст: {news['contents'][:4000]}"""

# 6. Генерація через Gemini з обробкою помилки 503 (перевантаження)
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

# 7. Виправлення пробілів у посиланні та відправка у Discord
safe_url = news['url'].replace(" ", "%20")

data = {
    "content": f"{response_text}\n\nОригінал: {safe_url}"
}
res = requests.post(WEBHOOK_URL, json=data)

if res.status_code == 204:
    print("Успішно відправлено в Discord!")
else:
    print(f"Помилка відправки в Discord: {res.text}")
