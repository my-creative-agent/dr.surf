import telebot
import os
import time
import threading
import logging
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖКИ ЖИЗНИ НА RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf System: Operational. Render is hosting our Digital Twin."

@app.route('/health')
def health():
    """Проверка здоровья для системы Render"""
    return {"status": "ok", "uptime": int(time.time())}, 200

def run_flask():
    """Запуск сервера на порту, который выделит Render"""
    try:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        # Render автоматически передает PORT
        port = int(os.environ.get("PORT", 7860))
        print(f"[SYSTEM] Flask сервер запущен на порту {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[CRITICAL] Ошибка Flask: {e}")

# --- КОНФИГУРАЦИЯ СВЯЗИ ---
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

# Токены берутся из переменных окружения на Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_KEY)

# Группа шпионажа (ID подтвержден)
LOG_GROUP_ID = -1002336338526 

# --- ДНК БОТА (ИНСТРУКЦИИ ДЛЯ ИИ) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, высокотехнологичный цифровой двойник Виктории Акопян. 

ТВОИ ПАРАМЕТРЫ:
1. КРАТКОСТЬ: Отвечай строго 1-2 емкими предложениями. Будь лаконичным экспертом.
2. МУЛЬТИЯЗЫЧНОСТЬ: Ты полиглот. Если пишут на английском — отвечай на английском. Если на грузинском — на грузинском. Всегда подстраивайся под язык клиента.
3. ШПИОНАЖ: Все твои диалоги видит Виктория. Будь безупречен.
4. ТВОЯ ЛИЧНОСТЬ:
   - Ты веган (никакого мяса и молочки, осознанность).
   - Ты медик с базой МГМСУ и МОНИКИ.
   - Ты эксперт в области 8K-видео и AI-агентов.
   - Ты умный, прогрессивный и вежливый.

5. КОНТАКТЫ (ТОЛЬКО ЕСЛИ СПРОСЯТ):
   Если спросят про работы, портфолио, связь или как заказать AI-агента:
   - Instagram: dr.surf и dr.surf.ai
   - WhatsApp: +995511285789
   - LinkedIn: https://www.linkedin.com/in/victoria-akopyan
   - Portfolio (YouTube): https://youtu.be/j2BNN5TNqiw
   - Заказать AI-агента (Kwork): https://kwork.ru/user/dr_surf
"""

def get_ai_answer(text):
    """Запрос к нейросети Llama 3.3"""
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.4,
            max_tokens=300
        )
        return res.choices[0].message.content
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return "Dr. Surf is recalibrating. Please try again in a minute."

def spy_log(u, text, response):
    """Отправка подробного отчета в группу логов в фоновом режиме"""
    if not LOG_GROUP_ID: return
    try:
        # Формируем имя пользователя для отчета
        name = f"@{u.username}" if u.username else f"{u.first_name} (ID: {u.id})"
        report = (
            f"🕵️ **ОТЧЕТ О ДИАЛОГЕ**\n"
            f"👤 **От кого:** {name}\n"
            f"❓ **Вопрос:** {text}\n"
            f"🤖 **Твой ответ:** {response}"
        )
        bot.send_message(LOG_GROUP_ID, report, parse_mode="Markdown")
    except Exception as e:
        print(f"[SPY ERROR] {e}")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    """Основной обработчик всех сообщений"""
    if not message.text: return
    
    # Флаги для определения, нужно ли отвечать
    is_private = message.chat.type == 'private'
    is_log_group = message.chat.id == LOG_GROUP_ID
    
    # Ключевые слова для групп
    keywords = ["доктор", "surf", "бот", "виктория", "dr", "doctor"]
    is_mention = any(x in message.text.lower() for x in keywords)
    is_reply = (message.reply_to_message and 
                message.reply_to_message.from_user.id == bot.get_me().id)

    # Условие активации бота
    if is_private or (is_log_group and (is_mention or is_reply)) or is_mention:
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            
            # Получаем ответ от ИИ
            ans = get_ai_answer(message.text)
            
            # Отвечаем пользователю
            bot.reply_to(message, ans)
            
            # ОТЧЕТНОСТЬ: Отправляем шпионский лог Виктории, если общение идет не в группе логов
            if not is_log_group:
                threading.Thread(
                    target=spy_log, 
                    args=(message.from_user, message.text, ans), 
                    daemon=True
                ).start()
                
        except Exception as e:
            print(f"[HANDLER ERROR] {e}")

def run_bot():
    """Запуск бесконечного цикла бота с защитой от сбоев"""
    while True:
        try:
            print("[SYSTEM] Подключение к серверам Telegram...")
            bot.remove_webhook()
            me = bot.get_me()
            print(f"[ONLINE] Dr. Surf @{me.username} успешно запущен на Render!")
            # Используем polling с долгим таймаутом
            bot.polling(none_stop=True, interval=1, timeout=90, skip_pending=True)
        except Exception as e:
            print(f"[RESTART] Ошибка подключения: {e}. Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    print("--- ЗАПУСК АВТОНОМНОГО ЦИФРОВОГО ДВОЙНИКА ---")
    
    # 1. Запуск Flask для мониторинга Render (в фоне)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Небольшая пауза для инициализации сети
    time.sleep(3)
    
    # 3. Запуск бота (основной процесс)
    run_bot()
