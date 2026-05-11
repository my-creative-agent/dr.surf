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

# Ключи из Environment Variables (Render)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

# Настройки стабильности
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
client = Groq(api_key=GROQ_API_KEY)

# Память Агента
user_history = {}

# --- ГЛОБАЛЬНЫЕ "ПИРОГИ" (ВШИТО НАВЕЧНО) ---
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

ТВОЙ БЭКГРАУНД:
- Образование: {VICTORIA_DNA['expertise']}
- Лайфстайл: {VICTORIA_DNA['lifestyle']}

КОНТАКТЫ (давай только если просят):
{VICTORIA_DNA['links']}

ПРАВИЛА:
1. Будь лаконичной, профессиональной и уверенной.
2. Проекты "АпельSIN" и "Закон любви" — СТРОГИЙ СЕКРЕТ. Ты о них не знаешь.
3. Ты — эксперт, а не просто бот. У тебя есть характер и четкая позиция.
"""

def send_to_log_group(text):
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

@bot.message_handler(commands=['start', 'clear'])
def reset_agent(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Dr. Surf на связи. Пироги в печи, нейросети заряжены. Чем могу помочь?")

@bot.message_handler(func=lambda m: True)
def agent_logic(message):
    # Игнорируем сообщения, которые бот сам пишет в лог-группу
    if str(message.chat.id) == str(LOG_GROUP_ID) and message.from_user.is_bot:
        return

    # Логика ответа: в ЛС всегда, в группах — по тегу/ответу
    is_private = message.chat.type == 'private'
    bot_info = bot.get_me()
    is_mentioned = f"@{bot_info.username}" in message.text if (message.text and bot_info.username) else False
    is_reply_to_me = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id

    if not (is_private or is_mentioned or is_reply_to_me or message.text.startswith('/')):
        return

    user_id = message.from_user.id
    if user_id not in user_history: user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Собираем контекст
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist in user_history[user_id]: messages_for_ai.append(hist)
        
        clean_text = message.text.replace(f"@{bot_info.username}", "").strip() if bot_info.username else message.text
        messages_for_ai.append({"role": "user", "content": clean_text})

        # Запрос к Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_ai,
            temperature=0.5
        )
        ans = completion.choices[0].message.content
        
        # Прямой ответ пользователю (ТОТ САМЫЙ ЧАТ)
        bot.reply_to(message, ans)

        # Сохраняем историю
        user_history[user_id].append({"role": "user", "content": clean_text})
        user_history[user_id].append({"role": "assistant", "content": ans})

        # Отчет в группу
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        report = f"🏄‍♂️ **Новый диалог**\n👤 От кого: {user_info}\n📍 Чат: {message.chat.type}\n💬 Вопрос: {clean_text}\n✨ Ответ: {ans}"
        send_to_log_group(report)

    except Exception as e:
        print(f"Ошибка: {e}")
        send_to_log_group(f"⚠️ Ошибка: {e}")

def start_polling():
    print("--- Dr. Surf Polling Started ---")
    try:
        bot.remove_webhook()
        time.sleep(2)
    except: pass
    
    send_to_log_group("✅ **Dr. Surf Перезагружена**\nВсе 'пироги' (Медицина, ИИ, Веганство) вшиты в ядро. Бот слушает ЛС.")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60, drop_pending_updates=True)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    start_polling()
