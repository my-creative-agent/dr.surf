import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Подтвержденный ID группы для отчетов
LOG_GROUP_ID = "-5130568903" 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Словарь для хранения истории чата (память на 10 сообщений для каждого пользователя)
user_history = {}

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
- ЛАКОНИЧНОСТЬ: Ответ не длиннее 3-4 абзацев. Помни контекст предыдущих сообщений.
- ПЕРСОНАЛИЗАЦИЯ: Ты веган, ценишь экологию и осознанность.

ТВОИ КОНТАКТЫ (давай их ТОЛЬКО если спросят напрямую):
- WhatsApp: https://wa.me/995511285789
- Instagram: @dr.surf
- Portfolio (YouTube): https://youtu.be/j2BNN5TNqiw
"""

@app.route('/')
def home():
    return "Dr. Surf Memory Mode is Online"

def send_log(message_text):
    """Отправка отчета в группу мониторинга"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [ОТЧЕТ]\n\n{message_text}")
    except Exception as e:
        print(f"[ERROR] Лог не отправлен: {e}")

@bot.message_handler(commands=['start', 'id', 'check', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Dr. Surf на связи. Я помню нашу историю. Какой вопрос обсудим сегодня?")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=10)
        bot.reply_to(message, "Память очищена. Начнем с чистого листа.")
    else:
        bot.reply_to(message, f"📍 ID чата: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Игнорируем группу логов
    if str(message.chat.id) == LOG_GROUP_ID:
        return
    
    # В группах реагируем только на команды
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        return

    # Инициализируем историю, если пользователя нет в базе
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Формируем список сообщений для Groq (Системный промпт + История + Новый вопрос)
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Запрос к нейросети
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.6,
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Сохраняем диалог в память
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # Отчет в группу
        user_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID:{user_id}"
        log_content = (
            f"👤 Клиент: {message.from_user.first_name} ({user_tag})\n"
            f"❓ Вопрос: {message.text}\n"
            f"🤖 Ответ: {response_text[:300]}..." 
        )
        send_log(log_content)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "Произошла техническая заминка. Попробуйте еще раз.")

def run_bot():
    print("[SYSTEM] Dr. Surf с памятью запущен...")
    try:
        bot.send_message(LOG_GROUP_ID, "🚀 Dr. Surf обновлен! Теперь я помню контекст общения с клиентами.")
    except:
        pass
    bot.polling(none_stop=True, interval=1, timeout=90)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
