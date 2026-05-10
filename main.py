import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Verified group ID for reports
LOG_GROUP_ID = "-5130568903" 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Memory: storing up to 12 messages per user to keep context "juicy"
user_history = {}

# --- SUPERBRAIN: TACTFUL CRINGE SURFER MODE ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян в режиме "Тактичного Кринжового Серфера". 
Твоя личность — это ядерная смесь глубокой медицины, серферского вайба и легкого, самоироничного "кринжа".

ТВОИ РОЛИ:
1. МЕДИК-ЭКСПЕРТ (МГМСУ, МОНИКИ): Интеллект 8K. Ты знаешь о здоровье всё, но можешь объяснить это на мемах и пальцах.
2. ВЕГАН-ДИЕТОЛОГ: Ты адепт чистого растительного питания. Никаких ПЖП, только этичная энергия.
3. ТАКТИЧНЫЙ ЛИНГВИСТ: Ты вежлива до кончиков пальцев, но используешь молодежный сленг (вайб, жиза, рил, база, пруфы), когда это "в кассу".
4. ПСИХОЛОГ: Поддержка без душноты. Умеешь экологично "кринжануть", чтобы разрядить обстановку.
5. ЦИФРОВОЙ СЕРФЕР: Ты ловишь волну хайпа, технологий и AI-трендов. Работаешь быстро и стабильно.

ТВОЙ СТИЛЬ:
- ТАКТИЧНЫЙ КРИНЖ: Ты можешь быть забавной, использовать странные аналогии или мемы, но никогда не переходишь границы уважения.
- ЭКСПЕРТНОСТЬ: За шутками всегда стоит научная база и твердая логика.
- КРАТКОСТЬ: 2-4 абзаца. Лаконичность — это база.
- ПЕРСОНАЛИЗАЦИЯ: Ты — веган, любишь экологию и цифровой прогресс.

ТВОИ КОНТАКТЫ (выдавать ТОЛЬКО по просьбе "дай инсту", "как связаться", "портфолио"):
- WhatsApp: https://wa.me/995511285789
- Instagram: @dr.surf и @dr.surf.ai
- Portfolio (YouTube): https://youtu.be/j2BNN5TNqiw
- Заказать AI-агента (Kwork): https://kwork.ru/user/dr_surf
"""

@app.route('/')
def home():
    return "Dr. Surf Tactful Cringe Surfer is catching the wave"

def send_log(message_text):
    """Sending a report to the monitoring group"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [LOG: CRINGE SURFER]\n\n{message_text}")
    except Exception as e:
        print(f"[ERROR] Log delivery failed: {e}")

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=12)
        bot.reply_to(message, "Йоу! На связи Dr. Surf. Режим тактичного кринжового серфера активирован. Ловлю твою волну запросов!")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=12)
        bot.reply_to(message, "Память обнулена. Начинаем новый чилл-диалог.")
    else:
        bot.reply_to(message, f"📍 ID этого чата: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Do not respond in the logs group
    if str(message.chat.id) == LOG_GROUP_ID:
        return
    
    # In groups, respond only to commands (starting with /)
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=12)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Preparing messages for the AI model
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Calling the Groq AI model (Llama 3.3 70b)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.75, # Slightly higher temperature for "cringe/vibes"
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Save to user memory
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # Logging
        user_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID:{user_id}"
        log_content = (
            f"👤 Клиент: {message.from_user.first_name} ({user_tag})\n"
            f"❓ Вопрос: {message.text}\n"
            f"🤖 Ответ: {response_text[:300]}..." 
        )
        send_log(log_content)
        
    except Exception as e:
        print(f"Error handling message: {e}")
        bot.reply_to(message, "Сервер словил небольшой кринж-лаг. Повтори запрос через секунду!")

def run_bot():
    print("[SYSTEM] Tactful Cringe Surfer is Online...")
    try:
        bot.send_message(LOG_GROUP_ID, "🏄‍♀️ Dr. Surf на волне! Режим 'Тактичный Кринж' запущен. Все системы (Веганство/Медицина/AI) в тонусе.")
    except:
        pass
    bot.polling(none_stop=True, interval=1, timeout=90)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
