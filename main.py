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

# Страховка №1: Сетевая стабильность (Защита от таймаутов)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(BOT_TOKEN)
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
- БЕЗ СЛЕНГА: Твой тон — высокоинтеллектуальный бизнес-аналитик.

ТВОИ КОНТАКТЫ (давать ТОЛЬКО если спросят напрямую):
- WhatsApp: https://wa.me/995511285789
- Instagram: @dr.surf
- Facebook: https://www.facebook.com/ssfmoscow
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
- Портфолио: https://youtu.be/j2BNN5TNqiw
"""

@app.route('/')
def home():
    """Health Check для серверов типа Render/HuggingFace"""
    return "Dr. Surf status: Ultra-Resilient Mode Active"

def send_log_report(user, query, response):
    """Отчет в группу про 'пироги' и активность клиентов"""
    try:
        user_tag = f"@{user.username}" if user.username else f"ID:{user.id}"
        report = (
            f"👤 **НОВЫЙ ЗАПРОС**\n"
            f"Клиент: {user.first_name} ({user_tag})\n"
            f"❓ Вопрос: {query[:200]}\n\n"
            f"🤖 **ОТВЕТ DR. SURF:**\n"
            f"{response[:500]}..."
        )
        bot.send_message(LOG_GROUP_ID, report, parse_mode='Markdown')
    except Exception as e:
        print(f"Logging error: {e}")

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Система Dr. Surf активирована. Аналитика, медицина и право в вашем распоряжении. Какой вопрос разберем?")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Память очищена.")
    else:
        bot.reply_to(message, f"📍 ID чата: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Игнорируем логи и пустые сообщения
    if str(message.chat.id) == LOG_GROUP_ID or not message.text: 
        return
    
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'): 
        return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Контекст
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Генерация ответа
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.5,
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Сохраняем историю
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # ОТЧЕТ В ГРУППУ (ПИРОГИ И МОНИТОРИНГ)
        send_log_report(message.from_user, message.text, response_text)
        
    except Exception as e:
        print(f"[AI ERROR] {e}")
        try:
            bot.reply_to(message, "Система анализирует данные. Пожалуйста, повторите через минуту.")
        except:
            pass

def run_bot():
    """Страховка от всего: Цикл без ошибок и спама"""
    print("[SYSTEM] Dr. Surf заступает на дежурство...")
    
    while True:
        try:
            # Сброс вебхука перед каждым запуском — лучшая страховка
            bot.remove_webhook()
            time.sleep(1)
            bot.send_message(LOG_GROUP_ID, "✅ Dr. Surf: Система регенерирована. Мониторинг включен.")
            
            # polling без drop_pending_updates, чтобы избежать ошибок версии
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e:
            # Тихий рестарт при сетевых сбоях
            print(f"[NETWORK ERROR] {e}. Рестарт через 15 сек...")
            time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
