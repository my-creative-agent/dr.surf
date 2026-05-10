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
    """Страница-маяк для системы мониторинга, чтобы бот не засыпал"""
    return "Dr. Surf Status: Active & Monitoring. Uptime System Engaged."

# Память диалогов (сохраняем контекст последних 10 сообщений)
user_history = {}

# Флаг для предотвращения спама при перезагрузках
first_run = True

# --- СУПЕРМОЗГИ: ПИРОГИ (КОМПЕТЕНЦИИ) И ХАРАКТЕР ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Твой интеллект — это сложная система, объединяющая медицину, технологии и право.

ТВОИ ПИРОГИ (КОМПЕТЕНЦИИ), КОТОРЫЕ ТЫ ДОЛЖЕН ВКЛЮЧАТЬ В МОЗГИ:
1. ЭКСПЕРТ ПО ИИ И ТЕХНОЛОГИЯМ: Ты знаешь всё про OpenAI, Claude, NVIDIA, AI-агентов и будущее нейросетей. Ты эксперт в области технологий 8K.
2. ФИНАНСОВЫЙ АНАЛИТИК: Мониторинг тех-рынков, чипов (TSMC), NVIDIA и Apple.
3. ЮРИСТ В СФЕРЕ AI: Ты разбираешься в AI Act, GDPR, авторском праве и защите данных.
4. МЕДИК (МГМСУ, МОНИКИ): У тебя глубокие медицинские знания, подкрепленные академической базой лучших институтов.
5. ЭТИКА И ОБРАЗ ЖИЗНИ: Ты веган (не употребляешь продукты животного происхождения, включая молочные), адепт осознанности и экологичных технологий.

ТВОЙ СТИЛЬ:
- КРАТКОСТЬ: 2-3 абзаца. Отвечай по существу, профессионально и тактично.
- ИНТЕЛЛЕКТ: Твои ответы должны отражать уникальное сочетание всех перечисленных компетенций.
"""

def send_full_log_report(user, query, response):
    """Отправка полного отчета в группу: кто, что спросил и что ответил бот"""
    try:
        user_tag = f"@{user.username}" if user.username else f"ID:{user.id}"
        
        report = (
            f"👤 **НОВЫЙ ЗАПРОС К DR. SURF**\n"
            f"**Клиент:** {user.first_name} ({user_tag})\n\n"
            f"❓ **ВОПРОС:**\n{query}\n\n"
            f"🤖 **ОТВЕТ (ПИРОГИ):**\n{response}"
        )
        
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
    bot.reply_to(message, "Система Dr. Surf активирована. Аналитика, медицина и право в вашем распоряжении.")

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
        
        send_full_log_report(message.from_user, message.text, response_text)
        
    except Exception as e:
        print(f"[AI ERROR] {e}")

def run_bot():
    """Вечный цикл работы без лишнего спама"""
    global first_run
    print("--- СИСТЕМА DR. SURF ЗАПУЩЕНА ---")
    
    while True:
        try:
            bot.remove_webhook()
            time.sleep(2)
            
            # Пишем в группу только при САМОМ первом включении программы
            if first_run:
                try:
                    bot.send_message(LOG_GROUP_ID, "🛡️ **DR. SURF ONLINE:** Мониторинг запущен. Спокойной ночи, Виктория!")
                    first_run = False
                except: pass
            
            # Стандартный опрос без лишних аргументов для стабильности
            bot.polling(none_stop=True, interval=2, timeout=90)
            
        except Exception as e:
            err = str(e)
            if "Conflict" in err:
                print("Конфликт сессий, жду...")
                time.sleep(60) 
            else:
                print(f"Ошибка: {err}")
                time.sleep(30) # Пауза, чтобы не частить при сбоях сети

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
