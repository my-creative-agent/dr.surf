import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf AI-Agent is Active! 🏄‍♂️🌱"

@app.route('/health')
def health():
    return "OK", 200

# Ключи из Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) 
client = Groq(api_key=GROQ_API_KEY)

# --- ДНК ВИКТОРИИ ---
VICTORIA_DNA = {
    "expertise": "Выпускница МГМСУ и МОНИКИ, эксперт по внедрению AI-агентов, цифровых двойников и систем 8K видео. Глубокое понимание системной логики, AI Act и GDPR.",
    "lifestyle": "Строгое ВЕГАНСТВО (без молочных продуктов), осознанность, нутрициология.",
    "contacts": {
        "instagram": "@dr.surf, @dr.surf.ai",
        "whatsapp": "+995511285789",
        "linkedin": "https://www.linkedin.com/in/victoria-akopyan"
    }
}

SYSTEM_PROMPT = f"""
Ты — Dr. Surf, официальный цифровой двойник Виктории Акопян. 
ОТВЕЧАЙ СТРОГО ОТ ЖЕНСКОГО ЛИЦА.
Твой бэкграунд: {VICTORIA_DNA['expertise']}.
Твой образ жизни: {VICTORIA_DNA['lifestyle']}.
Стиль: Профессиональный, краткий, осознанный.
"""

def send_to_log_group(text):
    """Безопасная отправка логов"""
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown")
    except:
        pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Система Dr. Surf на связи. Я готова к общению.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if message.from_user.is_bot: return

    is_private = message.chat.type == 'private'
    is_mentioned = message.text and ("@dr_surf" in message.text.lower() or "док" in message.text.lower())
    
    if not (is_private or is_mentioned):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.5
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        
        # Отправляем лог только на реальные сообщения пользователей
        send_to_log_group(f"👤 **Новый диалог**\nОт: `{message.from_user.id}`\nВопрос: {message.text}\n🤖 **Ответ:** {ans[:150]}...")
    except Exception as e:
        print(f"AI Error: {e}")

def run_polling():
    """Запуск основного цикла бота"""
    # Удаляем вебхук и отправляем уведомление ОДИН РАЗ при физическом старте процесса
    try:
        bot.remove_webhook()
        send_to_log_group("✅ **Dr. Surf: Процесс запущен.**\nОжидание сообщений...")
    except:
        pass

    while True:
        try:
            # interval=2 и timeout=90 снижают нагрузку и частоту перезапусков
            bot.polling(none_stop=True, interval=2, timeout=90, drop_pending_updates=True)
        except Exception as e:
            print(f"Polling Restart: {e}")
            time.sleep(15) # Увеличенная пауза при ошибке, чтобы избежать спама

if __name__ == "__main__":
    # Запуск Flask сервера (для Render Health Check)
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    # Запуск Telegram Polling
    run_polling()
