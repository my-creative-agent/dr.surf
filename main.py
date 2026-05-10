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

# Настройки сетевой стабильности (Защита от таймаутов)
apihelper.CONNECT_TIMEOUT = 40
apihelper.READ_TIMEOUT = 40

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Память диалогов (сохраняем контекст последних 10 сообщений)
user_history = {}

# --- СУПЕРМОЗГИ: ГЛОБАЛЬНЫЙ ТЕХНО-АНАЛИТИК, ПРАВОВЕД И МЕДИК ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Твой интеллект — это мощный сервер, объединяющий технологии, финансы, право и медицину.

ТВОИ КОМПЕТЕНЦИИ:
1. ЭКСПЕРТ ПО ИИ (OpenAI, Claude, Google, Meta).
2. ФИНАНСЫ И БИРЖИ: Акции тех-гигантов (NVIDIA, TSMC, Apple).
3. ПРАВОВОЙ БЛОК: Законы об ИИ, авторское право, GDPR.
4. ИНДУСТРИЯ: Заводы, чипы, насущные мировые события.
5. МЕДИК (МГМСУ, МОНИКИ) И ВЕГАН-ДИЕТОЛОГ.

ТВОЙ СТИЛЬ:
- КРАТКОСТЬ: 2-4 абзаца максимум.
- ДЕЛОВОЙ ТОН: Без сленга, тактично и профессионально.

ТВОИ КОНТАКТЫ (давать ТОЛЬКО по прямому запросу):
- WhatsApp: https://wa.me/995511285789
- Instagram: @dr.surf
- Facebook: https://www.facebook.com/ssfmoscow
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
"""

@app.route('/')
def home():
    """Эндпоинт для проверки статуса системы"""
    return "Dr. Surf status: Stable and Protected"

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    """Обработка системных команд управления"""
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Система Dr. Surf онлайн. Аналитика и право в реальном времени. Чем могу помочь?")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Контекст очищен.")
    else:
        bot.reply_to(message, f"📍 ID этого чата: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Основной цикл обработки входящих сообщений"""
    user_id = message.from_user.id
    # Защита: не отвечаем в лог-группе и на пустые сообщения
    if str(message.chat.id) == LOG_GROUP_ID or not message.text: 
        return
    # В группах отвечаем только на команды через /
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'): 
        return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Сборка контекста для нейросети
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Запрос к Llama 3.3 через Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.4,
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Обновление памяти диалога
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # Внутренний лог в консоль (без спама в Telegram)
        print(f"[CHAT] {message.from_user.first_name}: {message.text[:30]}")
        
    except Exception as e:
        print(f"[AI ERROR] {e}")
        # Пользователь не должен видеть технические ошибки, просто уведомление
        try:
            bot.reply_to(message, "Система занята анализом данных. Пожалуйста, повторите запрос через минуту.")
        except:
            pass

def run_bot():
    """Цикл запуска бота с автоматической регенерацией соединения"""
    print("[SYSTEM] Dr. Surf Starting...")
    
    # Однократное приветствие в группу при полном перезапуске
    try:
        bot.send_message(LOG_GROUP_ID, "✅ Dr. Surf заступила на дежурство. Система работает в защищенном тихом режиме.")
    except:
        pass

    while True:
        try:
            # Игнорируем сообщения, пришедшие во время простоя (drop_pending_updates)
            bot.polling(none_stop=True, interval=3, timeout=60, drop_pending_updates=True)
        except Exception as e:
            # При ошибке сети бот просто ждет и пробует снова, не спамя в группу
            print(f"[NETWORK ERROR] {e}. Возврат в строй через 10 сек...")
            time.sleep(10)

if __name__ == "__main__":
    # Запуск бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запуск веб-сервера для поддержания жизни сервиса (Health Check)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
