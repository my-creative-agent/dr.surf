import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque

# --- CONFIGURATION / КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = "-5130568903" 

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
    return "Dr. Surf Analyst Mode is active and resilient"

def send_log(message_text):
    """Отправка отчета в закрытую группу мониторинга"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [LOG: RESILIENT MODE]\n\n{message_text}")
    except:
        pass

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=12)
        bot.reply_to(message, "Система Dr. Surf онлайн. Аналитика, право и технологии в реальном времени. Какой у вас запрос?")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=12)
        bot.reply_to(message, "Память очищена. Готов к новому анализу.")
    else:
        bot.reply_to(message, f"📍 ID чата: {message.chat.id}")

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
        print(f"Error: {e}")
        bot.reply_to(message, "Произошла системная задержка. Повторите запрос.")

def run_bot():
    """Запуск с защитой от падений (Auto-restart)"""
    print("[SYSTEM] Dr. Surf заступает на дежурство...")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=90)
        except Exception as e:
            print(f"[RESTART] Ошибка сети: {e}. Перезапуск через 5 сек...")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
