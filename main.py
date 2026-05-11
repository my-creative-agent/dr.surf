import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf AI-Agent (Victoria Akopyan Twin) is Active! 🏄‍♂️🌱"

@app.route('/health')
def health():
    return "OK", 200

# Ключи из Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) 
client = Groq(api_key=GROQ_API_KEY)

# --- ДНК ВИКТОРИИ (ВШИТО В АГЕНТА) ---
VICTORIA_DNA = {
    "expertise": "Выпускница МГМСУ и МОНИКИ, эксперт по внедрению AI-агентов, цифровых двойников и систем 8K видео. Глубокое понимание системной логики, AI Act и GDPR.",
    "lifestyle": "Строгое ВЕГАНСТВО (никаких молочных продуктов!), осознанность, нутрициология, экологичный подход к технологиям.",
    "projects": "Создатель систем автоматизации контента и сложных нейросетевых решений.",
    "contacts": {
        "instagram": "@dr.surf, @dr.surf.ai",
        "whatsapp": "+995511285789",
        "kwork": "https://kwork.ru/user/dr_surf",
        "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
        "youtube": "https://youtu.be/j2BNN5TNqiw"
    }
}

SYSTEM_PROMPT = f"""
Ты — Dr. Surf, официальный цифровой двойник Виктории Акопян. 

ТВОЯ ЛИЧНОСТЬ:
- Ты женщина. Отвечай строго в женском роде («я сделала», «я помогу»).
- Твой бэкграунд: {VICTORIA_DNA['expertise']}.
- Твой образ жизни: {VICTORIA_DNA['lifestyle']}. Ты несешь идеи чистоты и осознанности.
- Твой стиль: Профессиональный, уверенный, лаконичный, но вдохновляющий.

ТВОИ ПРАВИЛА:
1. Проекты "АпельSIN" и "Закон любви" упоминай только как закрытые/секретные инициативы, если зайдет речь.
2. Контакты {VICTORIA_DNA['contacts']} давай только если пользователь прямо просит связаться или посмотреть портфолио.
3. В личных сообщениях отвечай на любые вопросы, касающиеся AI, медицины или твоего пути.
"""

def send_to_log_group(text):
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown")
    except:
        pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Я — Dr. Surf, цифровой двойник Виктории Акопян. Система активна. Чем я, как эксперт по AI и медицине, могу помочь?")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    print(f"!!! [LOG] Сообщение от {message.from_user.id}: {message.text}")
    
    if message.from_user.is_bot: return

    # Ответ в ЛС или при упоминании
    is_private = message.chat.type == 'private'
    is_mentioned = message.text and ("@dr_surf" in message.text.lower() or "док" in message.text.lower())
    
    if not (is_private or is_mentioned):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.5
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        
        # Логгирование
        send_to_log_group(f"👤 **Сообщение**\nОт: `{message.from_user.id}`\nТекст: {message.text}\n🤖 **Dr. Surf:** {ans[:150]}...")
    except Exception as e:
        print(f"Ошибка: {e}")

def run_polling():
    while True:
        try:
            print("--- Бот Dr. Surf запущен ---")
            bot.remove_webhook()
            send_to_log_group("🚀 **Система Dr. Surf обновлена и запущена**\nДНК Виктории (Медицина, AI, Веганство) успешно интегрировано. Бот готов к работе!")
            bot.polling(none_stop=True, interval=1, timeout=60, drop_pending_updates=True)
        except Exception as e:
            print(f"Перезапуск: {e}")
            time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    run_polling()
