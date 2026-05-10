import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque
from telebot import apihelper

# --- CONFIGURATION / КОНФИГУРАЦИЯ ---
# Все токены берутся из переменных окружения для безопасности
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = "-5130568903" 

# Страховка №1: Сетевая стабильность
# Увеличиваем таймауты, чтобы бот не отключался при медленном интернете
apihelper.CONNECT_TIMEOUT = 50
apihelper.READ_TIMEOUT = 50

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Память диалогов: Dr. Surf помнит контекст (последние 10 реплик)
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
    """Страховка №2: Health Check для предотвращения 'засыпания' сервера"""
    return "Dr. Surf status: Ultra-Resilient Mode Active"

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Система Dr. Surf активирована. Глобальная аналитика, медицина и право в вашем распоряжении. Какой вопрос разберем?")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Контекстная память успешно очищена.")
    else:
        bot.reply_to(message, f"📍 ID чата: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Игнорируем технические сообщения в лог-группе
    if str(message.chat.id) == LOG_GROUP_ID or not message.text: 
        return
    
    # Работа в группах: ответ только на команды или упоминания
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'): 
        return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Формируем запрос с учетом истории
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Запрос к топовой модели Llama 3.3 70B
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.5,
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Сохраняем в память
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
    except Exception as e:
        print(f"[AI ERROR] {e}")
        # Тихая обработка ошибок для пользователя
        try:
            bot.reply_to(message, "Система обрабатывает большой объем данных. Пожалуйста, повторите запрос через минуту.")
        except:
            pass

def run_bot():
    """Страховка №3: Бесконечный цикл регенерации без спама"""
    print("[SYSTEM] Dr. Surf заступает на дежурство...")
    
    # Очистка старых настроек при старте
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.send_message(LOG_GROUP_ID, "✅ Dr. Surf онлайн. Система защиты от сбоев активирована.")
    except:
        pass

    while True:
        try:
            # Запуск основного процесса
            bot.polling(none_stop=True, interval=3, timeout=60)
        except Exception as e:
            # Если упал — молча ждем и встаем сами (лог только в консоль)
            print(f"[NETWORK ERROR] {e}. Авто-рестарт через 15 секунд...")
            time.sleep(15)

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке (Thread)
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запускаем Flask для внешнего мониторинга Uptime
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
