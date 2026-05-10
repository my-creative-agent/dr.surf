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
apihelper.CONNECT_TIMEOUT = 100
apihelper.READ_TIMEOUT = 100

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Память диалогов (10 сообщений)
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

@app.route('/')
def home():
    return "Dr. Surf status: Monitoring & Reporting Active"

def send_log_report(user, query, response="Обработка..."):
    """Отчет в группу про 'пироги' и активность клиентов"""
    try:
        user_tag = f"@{user.username}" if user.username else f"ID:{user.id}"
        report = (
            f"👤 **ОТЧЕТ ПО ПИРОГАМ**\n"
            f"**Клиент:** {user.first_name} ({user_tag})\n"
            f"**Запрос:** {query[:300]}\n"
            f"**Статус:** ✅ Успешно ответил"
        )
        # Отправляем краткий лог сразу
        bot.send_message(LOG_GROUP_ID, report)
    except Exception as e:
        print(f"Logging error: {e}")

@bot.message_handler(commands=['start', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Система Dr. Surf готова. Аналитика и медицина в строю.")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Защита от само-логирования
    if str(message.chat.id) == LOG_GROUP_ID: return
    
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Подготовка контекста
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Запрос к ИИ
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.5
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Сохранение истории
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # ГАРАНТИРОВАННЫЙ ОТЧЕТ
        send_log_report(message.from_user, message.text, response_text)
        
    except Exception as e:
        print(f"[ERROR] {e}")

def run_bot():
    """Защита от всего: ловит Conflict и восстанавливает отчеты"""
    print("--- ЗАПУСК СИСТЕМЫ МОНИТОРИНГА ---")
    
    while True:
        try:
            # Очистка старых обновлений, чтобы не спамить при старте
            bot.remove_webhook()
            time.sleep(5)
            
            # Уведомление в группу о перезагрузке
            bot.send_message(LOG_GROUP_ID, "🛡️ **СИСТЕМА ЗАЩИТЫ:** Dr. Surf перезагружен. Все 'пироги' под контролем.")
            
            bot.polling(none_stop=True, interval=3, timeout=100)
        except Exception as e:
            err = str(e)
            if "Conflict" in err:
                print("!!! КОНФЛИКТ СЕССИЙ !!!")
                # Специальное уведомление в лог-группу при конфликте
                try:
                    bot.send_message(LOG_GROUP_ID, "⚠️ **ВНИМАНИЕ:** Обнаружена вторая копия бота. Пытаюсь нейтрализовать...")
                except: pass
                time.sleep(40) 
            else:
                print(f"Сбой: {err}")
                time.sleep(20)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
