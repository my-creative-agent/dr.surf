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
# Фиксированный ID твоей группы логов
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5130568903") 

# Максимальная стабильность
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)

# Память контекста
user_history = {}

# --- ОБНОВЛЕННОЕ ДНК (ЖЕНСКИЙ ПОЛ + ВСЕ ПИРОГИ) ---
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
2. СЕКРЕТНОСТЬ: Не разбазаривай ссылки. Давай их только если спросят прямо.
3. ВЫДАЧА КОНТАКТОВ (ПО ЗАПРОСУ):
   - Insta: @dr.surf / @dr.surf.ai
   - WhatsApp: +995511285789
   - Facebook: https://www.facebook.com/ssfmoscow
   - Kwork: https://kwork.ru/user/dr_surf
   - Портфолио: https://youtu.be/j2BNN5TNqiw
4. ТАЙНА ПРОЕКТОВ: "АпельSIN" и "Закон любви" — СЕКРЕТ. Ты о них не слышала.
"""

def send_to_group(text):
    """Отправка отчета в группу логов с проверкой ошибок"""
    try:
        # Принудительно очищаем текст от лишних пробелов и отправляем
        bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown", disable_web_page_preview=True)
        print(f"[SUCCESS] Сообщение отправлено в группу {LOG_GROUP_ID}")
    except Exception as e:
        print(f"[CRITICAL ERROR] Не удалось отправить в группу: {e}")

@bot.message_handler(commands=['start', 'clear', 'hunt'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/hunt'):
        bot.reply_to(message, "🎯 Поняла, Виктория. Я выхожу на мониторинг вакансий. Отчеты пришлю в группу.")
        send_to_group("🎯 **ХАНТЕР АКТИВИРОВАН**: Поиск по AI, 8K и Медицине запущен.")
        return
    
    user_history[user_id] = deque(maxlen=10)
    bot.reply_to(message, "Система Dr. Surf активирована. Я загрузила все знания: от анатомии до космологии. Чем могу помочь?")

@bot.message_handler(func=lambda m: True)
def handle_conversation(message):
    # Игнорируем сообщения из группы логов
    if str(message.chat.id) == str(LOG_GROUP_ID):
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
            temperature=0.3
        )
        ans = completion.choices[0].message.content
        
        bot.reply_to(message, ans)

        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": ans})

        # Формируем отчет
        user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
        report = (
            f"🏝 **DR. SURF: ОТЧЕТ**\n"
            f"👤 **От:** {message.from_user.first_name} ({user_info})\n"
            f"💬 **Вопрос:** {message.text}\n"
            f"🤖 **Ответ:** {ans}"
        )
        send_to_group(report)
        
    except Exception as e:
        print(f"[ERROR] Обработка сообщения: {e}")

def start_polling():
    """Запуск бота с жестким сбросом всех соединений"""
    print("--- Dr. Surf & Hunter System Online ---")
    while True:
        try:
            # ЖЕСТКИЙ СБРОС: удаляем вебхук и все старые сообщения
            bot.remove_webhook(drop_pending_updates=True)
            time.sleep(2)
            
            # Проверочный сигнал
            send_to_group("🚀 **СИСТЕМА ПЕРЕЗАПУЩЕНА**\nЯ на связи, женский род и все компетенции активны. Проверяю связь...")
            
            bot.polling(none_stop=True, interval=1, timeout=90)
        except Exception as e:
            print(f"[RESTART ERROR] Ошибка связи, пробую снова через 10с: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Flask для Render (порт 10000)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    start_polling()
