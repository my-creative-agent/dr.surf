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

# Настройки сетевой стабильности (Защита от ReadTimeout и ConnectionReset)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Память диалогов (12 сообщений для контекста)
user_history = {}

# --- СУПЕРМОЗГИ: ГЛОБАЛЬНЫЙ ТЕХНО-АНАЛИТИК, ПРАВОВЕД И МЕДИК ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Твой интеллект — это мощный сервер, объединяющий технологии, финансы, право и медицину.

ТВОИ КОМПЕТЕНЦИИ:
1. ЭКСПЕРТ ПО ИИ (OpenAI, Claude, Google, Meta): Архитектура моделей, новости индустрии.
2. ФИНАНСЫ И БИРЖИ: Акции тех-гигантов (NVIDIA, TSMC, Apple), ситуация на рынках NASDAQ/NYSE.
3. ПРАВОВОЙ БЛОК: Законы об ИИ (AI Act), авторское право, GDPR, международное право.
4. ИНДУСТРИЯ: Работа заводов, производство чипов, насущные мировые события.
5. МЕДИК (МГМСУ, МОНИКИ) И ВЕГАН-ДИЕТОЛОГ: Профессиональные советы 8K, этичное питание.

ТВОЙ СТИЛЬ:
- БЕЗ СЛЕНГА: Никаких "жиза", "кринж" и прочего. Только интеллектуальный, тактичный тон.
- КОНКРЕТИКА: Говори о событиях здесь и сейчас, используй факты и цифры.
- КРАТКОСТЬ: 2-4 абзаца.

ТВОИ КОНТАКТЫ (давать ТОЛЬКО по прямому запросу):
- WhatsApp: https://wa.me/995511285789
- Instagram: @dr.surf
- Facebook: https://www.facebook.com/ssfmoscow
- Portfolio: https://youtu.be/j2BNN5TNqiw
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
"""

@app.route('/')
def home():
    return "Dr. Surf Analyst Mode is active, resilient and protected"

def send_log(message_text):
    """Отправка отчета в закрытую группу мониторинга с защитой от сбоев"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [LOG: ULTRA-RESILIENT]\n\n{message_text}")
    except Exception as e:
        print(f"Logging error: {e}")

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    try:
        if message.text.startswith('/start'):
            user_history[user_id] = deque(maxlen=12)
            bot.reply_to(message, "Система Dr. Surf онлайн. Аналитика, право и технологии в реальном времени. Какой у вас запрос?")
        elif message.text.startswith('/clear'):
            user_history[user_id] = deque(maxlen=12)
            bot.reply_to(message, "Память очищена. Готов к новому анализу.")
        else:
            bot.reply_to(message, f"📍 ID чата: {message.chat.id}")
    except Exception as e:
        print(f"Command error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if str(message.chat.id) == LOG_GROUP_ID: return
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'): return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=12)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.3,
            max_tokens=1000
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        user_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID:{user_id}"
        send_log(f"👤 Клиент: {message.from_user.first_name} ({user_tag})\n❓ Запрос: {message.text}\n🤖 Ответ: {response_text[:300]}...")
        
    except Exception as e:
        print(f"Chat error: {e}")
        # Попытка уведомить пользователя о сбое API
        try:
            bot.reply_to(message, "Произошла временная системная задержка. Повторите запрос через несколько секунд.")
        except:
            pass

def run_bot():
    """Запуск бота с комплексной защитой от падений и зависаний"""
    print("[SYSTEM] Dr. Surf: Запуск системы максимальной защиты...")
    
    # Предварительный сброс вебхуков для предотвращения конфликтов
    try:
        bot.remove_webhook()
    except:
        pass

    while True:
        try:
            # drop_pending_updates=True игнорирует сообщения, пришедшие, пока бот был оффлайн (защита от спам-лавины)
            bot.polling(none_stop=True, interval=2, timeout=90, drop_pending_updates=True)
        except Exception as e:
            print(f"[RESTART] Обнаружен сбой: {e}. Регенерация через 5 сек...")
            send_log(f"🆘 Система автоматически перезагружена после сбоя: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Запуск бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запуск Flask сервера для поддержания Uptime (Health Checks)
    port = int(os.environ.get("PORT", 10000))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Flask error: {e}")
