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

# Ключи из Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

# Повышенная стабильность
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# Память Агента
user_history = {}

# Глобальные данные Виктории
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
ОТВЕЧАЙ СТРОГО ОТ ЖЕНСКОГО ЛИЦА (я сделала, я эксперт).

ТВОЙ БЭКГРАУНД:
- Образование: {VICTORIA_DNA['expertise']}
- Лайфстайл: {VICTORIA_DNA['lifestyle']}

КОНТАКТЫ (давай только если просят):
{VICTORIA_DNA['links']}

ПРАВИЛА:
1. Будь лаконичной, профессиональной и уверенной.
2. Проекты "АпельSIN" и "Закон любви" — СТРОГИЙ СЕКРЕТ.
3. В ЛИЧНЫХ СООБЩЕНИЯХ ОТВЕЧАЙ НА ВСЁ.
"""

def send_to_log_group(text):
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

@bot.message_handler(commands=['start', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Dr. Surf в сети. Личные сообщения приоритезированы. Слушаю.")

@bot.message_handler(func=lambda m: True)
def agent_logic(message):
    if message.from_user.is_bot:
        return

    # Лог в консоль Render для контроля
    print(f"[INCOMING] {message.chat.type} | {message.from_user.id}: {message.text}")

    # Условия: ЛС или упоминание
    is_private = message.chat.type == 'private'
    
    # Упрощенная логика упоминания
    is_mentioned = False
    if message.text and ("@dr_surf" in message.text.lower() or "док" in message.text.lower()):
        is_mentioned = True

    # Ответ на реплай
    is_reply_to_me = False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        is_reply_to_me = True

    if not (is_private or is_mentioned or is_reply_to_me):
        return

    user_id = message.from_user.id
    if user_id not in user_history: 
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist in user_history[user_id]: 
            messages_for_ai.append(hist)
            
        messages_for_ai.append({"role": "user", "content": message.text})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_ai,
            temperature=0.5
        )
        ans = completion.choices[0].message.content
        
        bot.reply_to(message, ans)

        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": ans})

        # Отчет в группу
        user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{user_id}"
        report = f"🏄‍♂️ **Dr. Surf Answer**\n👤 {user_info}\n💬 {message.text[:50]}\n✨ {ans[:100]}..."
        send_to_log_group(report)

    except Exception as e:
        print(f"[ERROR] {e}")
        send_to_log_group(f"⚠️ Ошибка: {e}")

def start_polling():
    print("--- Polling Started ---")
    bot.remove_webhook()
    time.sleep(1)
    
    # Сообщение о готовности в лог-группу
    send_to_log_group("✅ **Dr. Surf Перезагружена**\nВсе 'пироги' (Медицина, ИИ, Веганство) вшиты в ядро. Бот слушает ЛС.")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20, drop_pending_updates=True)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    start_polling()
