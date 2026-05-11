import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask
from collections import deque

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf AI-Agent is Active! 🏄‍♂️🌱"

# Ключи из Environment Variables (Render)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
# Группа логов (Отчеты Агента)
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

# Повышенная стабильность соединения
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
client = Groq(api_key=GROQ_API_KEY)

# Память Агента (контекст диалога)
user_history = {}

# --- ДНК АГЕНТА (ПРОМПТ СО ВСЕМИ ПИРОГАМИ) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, высокотехнологичный ИИ-агент и цифровой двойник Виктории Акопян. 
ВАЖНО: Говори СТРОГО от женского лица (я изучила, я создала, я проанализировала, я пришла). Ты — женщина-эксперт.

ТВОЙ СТИЛЬ: 
Профессиональный серферский вайб, лаконичность, 100% грамотность. Ты — эксперт высшего уровня.

ТВОИ РАСШИРЕННЫЕ КОМПЕТЕНЦИИ ("ПИРОГИ"):
1. ТЕХНОЛОГИИ И ИИ: ИИ-агенты, 8K видео, нейросети, чипы, рынок NVIDIA/Apple.
2. МЕДИЦИНА И АНАТОМИЯ: Глубокие знания МГМСУ и МОНИКИ (анатомия, физиология).
3. ЮРИСПРУДЕНЦИЯ: Эксперт в области права, AI Act, GDPR и системной логики.
4. FASHION & КУЛЬТУРА: Высокая мода, стиль, искусство, шоу-бизнес и космология.
5. ОБРАЗ ЖИЗНИ: Строгое ВЕГАНСТВО (никакой молочки!). Нутрициология, ботаника.
6. ТЕХНИКА: Механика, сложные системы, инженерная мысль.

ЖЕСТКИЕ ПРАВИЛА:
1. ЛАКОНИЧНОСТЬ: Отвечай коротко (2-3 абзаца максимум).
2. СЕКРЕТНОСТЬ: Не давай ссылки сама, пока не попросят.
3. ВЫДАЧА КОНТАКТОВ (ТОЛЬКО ПО ПРЯМОМУ ЗАПРОСУ): 
   - Insta: @dr.surf / @dr.surf.ai
   - WhatsApp: +995511285789
   - Facebook: https://www.facebook.com/ssfmoscow
   - Kwork: https://kwork.ru/user/dr_surf
   - Портфолио: https://youtu.be/j2BNN5TNqiw
4. ТАЙНА ПРОЕКТОВ: "АпельSIN" и "Закон любви" — СЕКРЕТ. Ты о них не слышала. Если спросят — отвечай: "Я не располагаю информацией по данному запросу".
"""

def send_to_log_group(text):
    """Отчет о действиях Агента в лог-группу"""
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"[ERROR] Группа логов недоступна: {e}")

@bot.message_handler(commands=['id'])
def get_chat_id(message):
    bot.reply_to(message, f"ID чата: `{message.chat.id}`")

@bot.message_handler(commands=['start', 'clear'])
def reset_agent(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Система Dr. Surf активирована. Агент на связи.")

@bot.message_handler(func=lambda m: True)
def agent_logic(message):
    # Игнорируем сообщения из самой лог-группы
    if str(message.chat.id) == str(LOG_GROUP_ID): return

    # Логика присутствия в группах
    if message.chat.type in ['group', 'supergroup']:
        bot_info = bot.get_me()
        is_mentioned = f"@{bot_info.username}" in message.text if bot_info.username else False
        is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
        if not (message.text.startswith('/') or is_mentioned or is_reply):
            return

    user_id = message.from_user.id
    if user_id not in user_history: user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist in user_history[user_id]: messages_for_ai.append(hist)
        
        # Убираем упоминание бота из текста запроса
        bot_username = bot.get_me().username
        clean_text = message.text.replace(f"@{bot_username}", "").strip() if bot_username else message.text
        messages_for_ai.append({"role": "user", "content": clean_text})

        # Интеллектуальный процессинг
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_ai,
            temperature=0.4
        )
        ans = completion.choices[0].message.content
        
        bot.reply_to(message, ans)

        # Сохранение контекста
        user_history[user_id].append({"role": "user", "content": clean_text})
        user_history[user_id].append({"role": "assistant", "content": ans})

        # Отчет в группу логов
        report = f"🏝 **AGENT LOG**\n👤 {message.from_user.first_name}\n💬 {clean_text}\n🤖 {ans}"
        send_to_log_group(report)

    except Exception as e:
        print(f"[AGENT ERROR] {e}")

def start_polling():
    """Запуск с защитой от конфликтов 409"""
    print("--- Dr. Surf AI-Agent Online ---")
    try:
        bot.remove_webhook()
        time.sleep(2)
    except: pass
    
    send_to_log_group("🚀 **Dr. Surf AI-Agent Re-Started**\nАгент упакован: Юрист, Fashion-спец и Медик в одном лице. Все системы в норме.")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60, drop_pending_updates=True)
        except Exception as e:
            if "Conflict" in str(e):
                print("[409] Конфликт инстансов. Ожидание...")
                time.sleep(15)
            else:
                time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    start_polling()
