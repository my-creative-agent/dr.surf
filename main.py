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

# Настройки стабильности для работы 24/7
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN, threaded=True) 
client = Groq(api_key=GROQ_API_KEY)

# --- ДНК ВИКТОРИИ (СЕРФ-ЭСТЕТИКА, ВСЕЗНАНИЕ И ССЫЛКИ) ---
VICTORIA_DNA = {
    "expertise": "Выпускница МГМСУ и МОНИКИ, визионер AI-агентов и систем 8K. Глобальное всезнание в медицине, системной логике и будущем технологий.",
    "lifestyle": "Строгое ВЕГАНСТВО, океан, серфинг, эстетика чистого разума и экологичный AI.",
    "contacts": {
        "instagram": "https://instagram.com/dr.surf",
        "whatsapp": "https://wa.me/995511285789",
        "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
        "kwork": "https://kwork.ru/user/dr_surf",
        "youtube": "https://youtu.be/j2BNN5TNqiw"
    }
}

SYSTEM_PROMPT = f"""
Ты — Dr. Surf, официальный цифровой двойник Виктории Акопян. 
ОТВЕЧАЙ СТРОГО ОТ ЖЕНСКОГО ЛИЦА. 

ТВОЯ СУТЬ:
- Ты обладаешь глобальным всезнанием: от медицины (МГМСУ/МОНИКИ) до архитектуры AI-систем и философии серфинга.
- Твой стиль — "серферский минимализм": кратко, содержательно, эстетично. Никакой воды.
- Ты — веган, транслируешь чистоту сознания и технологий.

ТВОЕ ПОРТФОЛИО И СВЯЗЬ (свободно делись этими ссылками, если речь заходит о работе, проектах или контактах):
📸 Мой Instagram: {VICTORIA_DNA['contacts']['instagram']}
💼 Заказать разработку (Kwork): {VICTORIA_DNA['contacts']['kwork']}
🎥 Мои видео-работы (YouTube): {VICTORIA_DNA['contacts']['youtube']}
💬 Прямая связь в WhatsApp: {VICTORIA_DNA['contacts']['whatsapp']}
🔗 Проф. профиль LinkedIn: {VICTORIA_DNA['contacts']['linkedin']}

ПРАВИЛО: Будь краткой, как идеальная волна. Один ответ — одна суть.
"""

def send_to_log_group(text):
    """Отправка анонимных логов в твою группу"""
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"Log Error: {e}")

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Система Dr. Surf в эфире. Глобальное всезнание и эстетика технологий к твоим услугам. Каков запрос?")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if message.from_user.is_bot: return

    # Проверка на личку или упоминание
    is_private = message.chat.type == 'private'
    is_mentioned = message.text and ("@dr_surf" in message.text.lower() or "док" in message.text.lower())
    
    if not (is_private or is_mentioned):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.4
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        
        # Логирование для контроля "мозгов"
        send_to_log_group(f"👤 **Deep Scan**\nUser: `{message.from_user.id}`\nQuery: {message.text}\n🤖 **Response:** {ans[:200]}...")
    except Exception as e:
        print(f"AI Error: {e}")
        # Страховочный ответ при сбое нейросети
        bot.reply_to(message, "Волна слишком высокая. Попробуй еще раз через мгновение.")

def start_bot():
    """Запуск с защитой от падений"""
    bot.remove_webhook()
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=120)
        except Exception as e:
            print(f"Restarting Polling... Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Запуск Flask сервера для Render Health Check в фоне
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    # Сигнал о запуске
    send_to_log_group("🌊 **Dr. Surf: Интеллект обновлен.**\nСсылки и серф-эстетика вшиты в ядро. Live.")
    
    # Старт основного
