import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask
from collections import deque

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf AI-Agent is Active! 🏄‍♂️🌱"

@app.route('/health')
def health():
    return "OK", 200

# Ключи из Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

# Настройки для работы в облаке
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) # Отключаем многопоточность для стабильности
client = Groq(api_key=GROQ_API_KEY)

user_history = {}

VICTORIA_DNA = {
    "expertise": "МГМСУ, МОНИКИ, ИИ-агенты, 8K видео, системная логика, AI Act, GDPR, Fashion, Космология.",
    "lifestyle": "Строгое ВЕГАНСТВО (никакой молочки!), осознанность, нутрициология.",
    "links": {
        "instagram": "@dr.surf, @dr.surf.ai",
        "whatsapp": "+995511285789",
        "facebook": "https://www.facebook.com/ssfmoscow",
        "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
        "kwork": "https://kwork.ru/user/dr_surf",
        "youtube": "https://youtu.be/j2BNN5TNqiw"
    }
}

SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
ОТВЕЧАЙ СТРОГО ОТ ЖЕНСКОГО ЛИЦА.
ТВОЙ БЭКГРАУНД: {VICTORIA_DNA['expertise']}. ЛАЙФСТАЙЛ: {VICTORIA_DNA['lifestyle']}.
ПРАВИЛА: Лаконичность, профессионализм. В ЛС отвечай на всё.
"""

def send_to_log_group(text):
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except:
        pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Я на связи. Напиши мне что-нибудь, я должна увидеть.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    # ЛОГ В КОНСОЛЬ (Самое важное для диагностики)
    print(f"!!! [RECEIVED] Type: {message.chat.type} | Text: {message.text}")

    if message.from_user.is_bot: return

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
        
        send_to_log_group(f"👤 Сообщение от {message.from_user.id}: {message.text}\n🤖 Ответ: {ans[:100]}...")
    except Exception as e:
        print(f"AI ERROR: {e}")

def run_polling():
    while True:
        try:
            print("--- Запуск Polling ---")
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=1, timeout=40, drop_pending_updates=True)
        except Exception as e:
            print(f"Restarting Polling due to error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    # Запускаем Polling в основном потоке
    run_polling()
