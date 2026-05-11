import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask
from collections import deque

# --- CONFIGURATION ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf System is Active! 🏄‍♂️🌱"

# Ключи из Environment Variables на Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5130568903") 

# Настройки для стабильности
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

# Включаем потоковую обработку для скорости
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
client = Groq(api_key=GROQ_API_KEY)

# Память контекста
user_history = {}

# --- ДНК (ЦИФРОВОЙ ДВОЙНИК + ЖЕНСКИЙ ПОЛ) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
ВАЖНО: Говори СТРОГО от женского лица (я пришла, я увидела, я изучила). Ты — женщина-эксперт.

Стиль: Лаконичный, профессиональный серферский вайб. ГРАМОТНОСТЬ 100%.

ТВОИ РАСШИРЕННЫЕ КОМПЕТЕНЦИИ ("ПИРОГИ"):
1. ТЕХНОЛОГИИ И ИИ: ИИ-агенты, 8K видео, нейросети, чипы, рынок NVIDIA/Apple.
2. МЕДИЦИНА И АНАТОМИЯ: Глубокие знания МГМСУ и МОНИКИ. Анатомия и физиология.
3. ОБРАЗ ЖИЗНИ: Строгое ВЕГАНСТВО (никакой молочки!). Здоровое питание, нутрициология, ботаника.
4. КУЛЬТУРА И ДРАЙВ: Искусство, мода, шоу-бизнес, спорт, космология.
5. ТЕХНИКА: Механика (сложные системы), системная логика, юриспруденция (AI Act/GDPR).

ЖЕСТКИЕ ПРАВИЛА:
1. ЛАКОНИЧНОСТЬ: Отвечай коротко (2-3 абзаца максимум).
2. СЕКРЕТНОСТЬ (НЕ РАЗБАЗАРИВАТЬ): Не давай ссылки, соцсети или контакты сама. 
3. ВЫДАЧА КОНТАКТОВ (ТОЛЬКО ПО ПРЯМОМУ ЗАПРОСУ): Если спросят прямо:
   - Insta: @dr.surf / @dr.surf.ai | WhatsApp: +995511285789
   - Facebook: https://www.facebook.com/ssfmoscow
   - Kwork: https://kwork.ru/user/dr_surf
   - Портфолио: https://youtu.be/j2BNN5TNqiw
4. ТАЙНА ПРОЕКТОВ: "АпельSIN" и "Закон любви" — СЕКРЕТ. Ты о них не слышала. Если спросят — отвечай, что не понимаешь, о чем речь.
"""

def send_to_group(text):
    """Отправка отчета в группу логов"""
    try:
        bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"[ERROR] Группа логов: {e}")

@bot.message_handler(commands=['start', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Система Dr. Surf активирована. Я на связи. Чем могу помочь?")

@bot.message_handler(func=lambda m: True)
def handle_conversation(message):
    # Не отвечаем в группе логов
    if str(message.chat.id) == str(LOG_GROUP_ID):
        return

    # В группах отвечаем только если есть обращение (в личке отвечаем на всё)
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        return

    user_id = message.from_user.id
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist in user_history[user_id]:
            messages_for_ai.append(hist)
        messages_for_ai.append({"role": "user", "content": message.text})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_ai,
            temperature=0.4
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        print(f"[SUCCESS] Ответила пользователю {user_id}")

        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": ans})

        # Отчет в группу
        user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
        report = (
            f"🏝 **DR. SURF: ОТЧЕТ**\n"
            f"👤 **От:** {message.from_user.first_name} ({user_info})\n"
            f"💬 **Вопрос:** {message.text}\n"
            f"🤖 **Ответ:** {ans}"
        )
        send_to_group(report)
        
    except Exception as e:
        print(f"[ERROR] AI Error: {e}")

def start_polling():
    """Бесконечный цикл с защитой от вылета"""
    print("--- Dr. Surf System Online (Polling) ---")
    while True:
        try:
            # Самый простой и надежный запуск
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"[POLLING ERROR] {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Запуск Flask
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # Запуск Polling
    start_polling()
