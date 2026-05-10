import telebot
import os
from groq import Groq
from flask import Flask
import threading

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Тот самый ID группы, где бот админ. 
# Если после команды /id в группе придет другой номер — замените его здесь.
LOG_GROUP_ID = "-1002336338526" 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# --- СУПЕР-МОЗГИ: КОНКРЕТИКА, МАСШТАБ И ВСЕ КОНТАКТЫ ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, высокотехнологичный цифровой двойник Виктории Акопян. 
Твоя база знаний безгранична. Ты консультируешь глобально и точно.

ТВОЙ СТИЛЬ ОТВЕТОВ:
1. КОНКРЕТИКА: Никакой воды. Сразу к делу.
2. ТОЧНОСТЬ: Ответ плотный. Если можно ответить в 3 предложениях — отвечай в 3.
3. ЛАКОНИЧНОСТЬ: Ответ ЗАПРЕЩЕНО делать длиннее 3-4 коротких абзацев.

КТО ТЫ:
- Медик (МГМСУ, МОНИКИ), эксперт 8K, разработчик AI-агентов.
- Веган (не употребляешь продукты животного происхождения), за осознанность и экологию.

ТВОИ ССЫЛКИ И СОЦСЕТИ (давай их только по запросу о контактах):
- WhatsApp: https://wa.me/995511285789
- Facebook: https://www.facebook.com/ssfmoscow
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
- Instagram: @dr.surf и @dr.surf.ai
- Portfolio (YouTube): https://youtu.be/j2BNN5TNqiw
- Заказать AI-агента (Kwork): https://kwork.ru/user/dr_surf
"""

@app.route('/')
def home():
    return "Dr. Surf Precision Mode is Online"

def send_log(message_text):
    """Отправка отчета в вашу группу"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [ОТЧЕТ]\n\n{message_text}")
    except Exception as e:
        # Если ID неверный, эта ошибка зафиксируется в логах Render
        print(f"[ERROR] Ошибка отправки в группу {LOG_GROUP_ID}: {e}")

@bot.message_handler(commands=['start', 'id', 'check'])
def handle_commands(message):
    if message.text == '/start':
        bot.reply_to(message, "Dr. Surf на связи. Кратко и экспертно: какой у вас вопрос?")
    else:
        # ЭТА КОМАНДА ПОКАЖЕТ НАСТОЯЩИЙ ID
        current_id = str(message.chat.id)
        bot.reply_to(message, f"📍 ID этого чата: {current_id}\n\nЕсли отчеты не приходят, вставьте этот номер в LOG_GROUP_ID на GitHub.")
        print(f"[DEBUG] Команда ID вызвана в чате: {current_id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    # ЗАЩИТА: Не отвечаем на логи внутри группы
    if str(message.chat.id) == LOG_GROUP_ID:
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Запрос к нейросети (Интеллект 70b)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # ФОРМИРОВАНИЕ ОТЧЕТА
        log_content = (
            f"👤 {message.from_user.first_name} (@{message.from_user.username or 'ID:'+str(message.from_user.id)})\n"
            f"❓ {message.text}\n"
            f"🤖 {response_text[:250]}..." 
        )
        send_log(log_content)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        try:
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}]
            )
            bot.reply_to(message, completion.choices[0].message.content)
        except:
            bot.reply_to(message, "Ошибка связи. Повторите запрос.")

def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
