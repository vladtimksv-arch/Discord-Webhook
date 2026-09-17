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

# 1. Чорний список (російські ЗМІ — блокуємо суворо)
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

print(f"Обробка новини від джерела: {feed_label}")

# 2. Промпт: переклад, винесення категорії в КІНЕЦЬ та розпізнавання світових медіа (IGN, PC Gamer тощо)
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

# 3. Відправка в Discord із правильним посиланням в кінці
safe_url = news['url'].replace(" ", "%20")

data = {
    "content": f"{response_text}\n\nОригінал: {safe_url}"
}
res = requests.post(WEBHOOK_URL, json=data)

if res.status_code == 204:
    print("Успішно відправлено в Discord!")
else:
    print(f"Помилка відправки в Discord: {res.text}")
