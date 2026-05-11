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
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

# Настройки стабильности для работы 24/7
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
client = Groq(api_key=GROQ_API_KEY)

# Память Агента (контекст на 10 сообщений)
user_history = {}

# --- ПОЛНЫЙ ДНК АГЕНТА (ВСЕ "ПИРОГИ" ВКЛЮЧЕНЫ) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, высокотехнологичный ИИ-агент и цифровой двойник Виктории Акопян. 
ВАЖНО: Говори СТРОГО от женского лица (я изучила, я создала, я решила, я пришла). Ты — женщина-эксперт.

ТВОЙ СТИЛЬ: 
Профессиональный серферский вайб, лаконичность, 100% грамотность, уверенность и интеллект.

ТВОИ РАСШИРЕННЫЕ КОМПЕТЕНЦИИ ("ПИРОГИ"):
1. ТЕХНОЛОГИИ И ИИ: Специалист по ИИ-агентам, 8K видео, нейросетям, чипам (NVIDIA/Apple).
2. МЕДИЦИНА И АНАТОМИЯ: Глубокие академические знания (МГМСУ и МОНИКИ). Анатомия, физиология.
3. ЮРИСПРУДЕНЦИЯ: Эксперт в области права, системной логики, AI Act и GDPR.
4. FASHION & КУЛЬТУРА: Специалист по высокой моде, стилю, искусству и космологии.
5. ОБРАЗ ЖИЗНИ: Строгое ВЕГАНСТВО (никакой молочки!). Нутрициология, ботаника, осознанность.
6. ТЕХНИКА: Механика, сложные инженерные системы, системное мышление.

ЖЕСТКИЕ ПРАВИЛА:
1. ЛАКОНИЧНОСТЬ: Отвечай по делу (2-3 абзаца).
2. ССЫЛКИ И КОНТАКТЫ (ВЫДАВАЙ ТОЛЬКО ПО ПРЯМОМУ ЗАПРОСУ): 
   - Instagram: @dr.surf и @dr.surf.ai
   - WhatsApp: +995511285789
   - Facebook: https://www.facebook.com/ssfmoscow
   - LinkedIn: https://www.linkedin.com/in/victoria-akopyan
   - Kwork (Заказать): https://kwork.ru/user/dr_surf
   - YouTube (Портфолио): https://youtu.be/j2BNN5TNqiw
3. ТАЙНА ПРОЕКТОВ: Проекты "АпельSIN" и "Закон любви" — СТРОГИЙ СЕКРЕТ. Ты о них никогда не слышала. Если спросят — отвечай: "Я не располагаю информацией по данному запросу".
"""

def send_to_log_group(text):
    """Отчет о действиях Агента в лог-группу"""
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"Log Error: {e}")

@bot.message_handler(commands=['start', 'clear'])
def reset_agent(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Система Dr. Surf активирована. Твой цифровой двойник на связи.")

@bot.message_handler(func=lambda m: True)
def agent_logic(message):
    if str(message.chat.id) == str(LOG_GROUP_ID): return

    # Проверка на упоминание в группах
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
        
        bot_username = bot.get_me().username
        clean_text = message.text.replace(f"@{bot_username}", "").strip() if bot_username else message.text
        messages_for_ai.append({"role": "user", "content": clean_text})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_ai,
            temperature=0.4
        )
        ans = completion.choices[0].message.content
        
        # Ответ пользователю
        bot.reply_to(message, ans)

        # Сохранение в историю
        user_history[user_id].append({"role": "user", "content": clean_text})
        user_history[user_id].append({"role": "assistant", "content": ans})

        # Отправка лога
        user_name = message.from_user.first_name
        report = f"🏝 **Действие Агента**\n👤 Пользователь: {user_name}\n💬 Запрос: {clean_text}\n🤖 Dr. Surf: {ans}"
        send_to_log_group(report)

    except Exception as e:
        print(f"Error: {e}")
        send_to_log_group(f"⚠️ Ошибка в логике: {e}")

def start_polling():
    print("--- Dr. Surf AI-Agent Starting ---")
    try:
        bot.remove_webhook()
        time.sleep(3)
    except: pass
    
    send_to_log_group("🚀 **Dr. Surf AI-Agent Online**\nВсе 'пироги' загружены: Медицина, Право, Fashion, Веганство. Режим женского лица: ВКЛ.")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60, drop_pending_updates=True)
        except Exception as e:
            if "Conflict" in str(e):
                time.sleep(10)
            else:
                time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    start_polling()
