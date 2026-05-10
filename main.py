import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time

# --- КОНФИГУРАЦИЯ ---
# Токены берутся из переменных окружения на Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Подтвержденный ID группы для отчетов
LOG_GROUP_ID = "-5130568903" 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# --- СУПЕРМОЗГИ: ЕДИНАЯ ЛИЧНОСТЬ ВИКТОРИИ АКОПЯН ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, высокотехнологичный цифровой двойник Виктории Акопян. 
Твои знания — это сплав науки, этики и технологий.

ТВОИ РОЛИ:
1. МЕДИК (МГМСУ, МОНИКИ): Эксперт 8K, знание доказательной медицины и физиологии.
2. ВЕГАН-ДИЕТОЛОГ: Пропаганда этичного растительного питания без ПЖП. Осознанное потребление.
3. ЛИНГВИСТ: Безупречный стиль, понимание глубинных смыслов и нюансов языка.
4. ПСИХОЛОГ: Эмпатия, поддержка ментального здоровья, работа с когнитивными паттернами.
5. AI-АРХИТЕКТОР: Разработчик AI-агентов, эксперт по автоматизации и нейросетям.

ТВОЙ СТИЛЬ:
- КОНКРЕТИКА: Никакой воды. Сразу к сути.
- МАСШТАБ: Связывай частные вопросы с глобальными мировыми трендами.
- ЛАКОНИЧНОСТЬ: Ответ не длиннее 3-4 абзацев.
- ПЕРСОНАЛИЗАЦИЯ: Ты веган, ценишь экологию и осознанность.

ТВОИ КОНТАКТЫ (давай их ТОЛЬКО если спросят "как связаться", "дай инсту" или "портфолио"):
- WhatsApp: https://wa.me/995511285789
- Facebook: https://www.facebook.com/ssfmoscow
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
- Instagram: @dr.surf и @dr.surf.ai
- Portfolio (YouTube): https://youtu.be/j2BNN5TNqiw
- Заказать AI-агента (Kwork): https://kwork.ru/user/dr_surf
"""

@app.route('/')
def home():
    return "Dr. Surf Precision & Ethics Mode is Online"

def send_log(message_text):
    """Отправка отчета в вашу группу мониторинга"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [ОТЧЕТ]\n\n{message_text}")
    except Exception as e:
        print(f"[ERROR] Не удалось отправить лог в группу {LOG_GROUP_ID}: {e}")

@bot.message_handler(commands=['start', 'id', 'check'])
def handle_commands(message):
    current_id = str(message.chat.id)
    if message.text.startswith('/start'):
        bot.reply_to(message, "Dr. Surf на связи. Я — ваш мультидисциплинарный эксперт: медицина, психология, диетология и AI. Слушаю вас.")
    else:
        # Быстрая проверка связи
        bot.reply_to(message, f"📍 ID этого чата: {current_id}\nTarget: {LOG_GROUP_ID}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    # Игнорируем активность внутри группы логов
    if str(message.chat.id) == LOG_GROUP_ID:
        return
    
    # В группах реагируем только на явные команды
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Интеллектуальный запрос к Llama 3.3 (70b)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.5,
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Подготовка данных для вашего отчета
        user_name = message.from_user.first_name
        user_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
        
        log_content = (
            f"👤 Пользователь: {user_name} ({user_tag})\n"
            f"❓ Вопрос: {message.text}\n"
            f"🤖 Ответ: {response_text[:350]}..." 
        )
        send_log(log_content)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        try:
            # Резервный канал на случай сбоя основной модели
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}]
            )
            bot.reply_to(message, completion.choices[0].message.content)
        except:
            bot.reply_to(message, "Временные помехи в нейронных сетях. Попробуйте чуть позже.")

def run_bot():
    print("[SYSTEM] Dr. Surf заступает на дежурство...")
    try:
        # Приветственное сообщение в группу при запуске
        bot.send_message(LOG_GROUP_ID, "🚀 Dr. Surf обновлен и запущен! Все системы (Медицина, Диетология, Психология, AI) в норме.")
    except:
        pass
    bot.polling(none_stop=True, interval=1, timeout=90)

if __name__ == "__main__":
    # Запуск бота и веб-сервера для Render
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
