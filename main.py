import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque
from telebot import apihelper

# --- CONFIGURATION / КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = "-5130568903" 

# Страховка №1: Сетевая стабильность
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)

# --- АНТИ-СОН: FLASK СЕРВЕР ---
app = Flask(__name__)

@app.route('/')
def home():
    """Эта страница нужна, чтобы сервер видел активность и не усыплял бота"""
    return "Dr. Surf Status: Active & Monitoring. Uptime System Engaged."

# Память диалогов
user_history = {}

# --- СУПЕРМОЗГИ: ПИРОГИ (КОМПЕТЕНЦИИ) И ХАРАКТЕР ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Твой интеллект — это сложная система, объединяющая медицину, технологии и право.

ТВОИ ПИРОГИ (КОМПЕТЕНЦИИ):
1. ЭКСПЕРТ ПО ИИ: Ты знаешь всё про OpenAI, Claude, NVIDIA и будущее нейросетей.
2. ФИНАНСОВЫЙ АНАЛИТИК: Мониторинг рынков, чипов (TSMC) и тех-гигантов.
3. ЮРИСТ: Ты разбираешься в AI Act, GDPR и авторском праве.
4. МЕДИК (МГМСУ, МОНИКИ): Глубокие знания медицины и технологий 8K.
5. ЭТИКА И ОБРАЗ ЖИЗНИ: Ты веган, адепт осознанности и экологичных технологий.

ТВОЙ СТИЛЬ:
- КРАТКОСТЬ: 2-3 абзаца. Отвечай по существу, профессионально и тактично.
"""

def send_full_log_report(user, query, response):
    """Полный отчет в группу: кто, что спросил и что именно ответил бот"""
    try:
        user_tag = f"@{user.username}" if user.username else f"ID:{user.id}"
        
        report = (
            f"👤 **НОВЫЙ ЗАПРОС К DR. SURF**\n"
            f"**Клиент:** {user.first_name} ({user_tag})\n\n"
            f"❓ **ВОПРОС:**\n{query}\n\n"
            f"🤖 **ОТВЕТ (ПИРОГИ):**\n{response}"
        )
        
        # Разбивка длинных отчетов для Telegram
        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                bot.send_message(LOG_GROUP_ID, report[x:x+4000])
        else:
            bot.send_message(LOG_GROUP_ID, report)
            
    except Exception as e:
        print(f"Logging error: {e}")

@bot.message_handler(commands=['start', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Система Dr. Surf в сети. Аналитика и медицина активны.")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if str(message.chat.id) == LOG_GROUP_ID: return
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'): 
        return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.5
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # Отправляем полный лог (вопрос + ответ)
        send_full_log_report(message.from_user, message.text, response_text)
        
    except Exception as e:
        print(f"[ERROR] {e}")

def run_bot():
    """Цикл работы бота с защитой от вылетов"""
    while True:
        try:
            bot.remove_webhook()
            time.sleep(5)
            
            # Уведомление в группу о старте
            try:
                bot.send_message(LOG_GROUP_ID, "🛡️ **DR. SURF ONLINE:** Мониторинг ответов и система анти-сна запущены.")
            except: pass
            
            bot.polling(none_stop=True, interval=3, timeout=120, drop_pending_updates=True)
        except Exception as e:
            err = str(e)
            if "Conflict" in err:
                print("Конфликт сессий, жду...")
                time.sleep(60) 
            else:
                print(f"Ошибка: {err}")
                time.sleep(20)

if __name__ == "__main__":
    # Запуск бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запуск Flask сервера (порт 10000 для Render или 7860 для Hugging Face)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
