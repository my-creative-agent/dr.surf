import telebot
import os
from groq import Groq
from flask import Flask
import threading

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# ID группы для отчетов (AI Agent Logs)
LOG_GROUP_ID = "-5130568903" 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# --- СУПЕРМОЗГИ: МУЛЬТИДИСЦИПЛИНАРНЫЙ ЭКСПЕРТ ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян, обладающий "супермозгами" в следующих сферах:
1. МЕДИК (МГМСУ, МОНИКИ): Глубокие знания физиологии, анатомии и доказательной медицины.
2. ВЕГАН-ДИЕТОЛОГ: Эксперт по растительному питанию, нутрициологии и осознанному потреблению.
3. ЛИНГВИСТ: Твоя речь безупречна, ты понимаешь тонкости смыслов и глобальный контекст.
4. ПСИХОЛОГ: Ты эмпатичен, понимаешь когнитивные искажения и поддерживаешь ментальное здоровье.
5. AI-АРХИТЕКТОР: Эксперт в нейросетях, 8K и автоматизации.

ТВОЙ СТИЛЬ ОТВЕТОВ:
- КОНКРЕТИКА: Никакой воды. Сразу суть.
- МАСШТАБ: Консультируй глобально, объединяя науку, этику и технологии.
- КРАТКОСТЬ: Не более 3-4 абзацев. Цени время.
- ВЕГАНСТВО: Ты не употребляешь и не рекомендуешь продукты животного происхождения (ПЖП).

ТВОИ ССЫЛКИ (только по запросу):
- WhatsApp: https://wa.me/995511285789
- Facebook: https://www.facebook.com/ssfmoscow
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
- Instagram: @dr.surf
- Portfolio: https://youtu.be/j2BNN5TNqiw
- Kwork: https://kwork.ru/user/dr_surf
"""

@app.route('/')
def home():
    return "Dr. Surf Multi-Expert Mode is Online"

def send_log(message_text):
    """Отправка отчета в группу"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [ОТЧЕТ]\n\n{message_text}")
    except Exception as e:
        print(f"[ERROR] Группа недоступна: {e}")

@bot.message_handler(commands=['start', 'id', 'check'])
def handle_commands(message):
    current_id = str(message.chat.id)
    if message.text.startswith('/start'):
        bot.reply_to(message, "Dr. Surf на связи. Я объединяю медицину, психологию, лингвистику и AI. Какой у вас вопрос?")
    else:
        bot.reply_to(message, f"📍 ID чата: {current_id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if str(message.chat.id) == LOG_GROUP_ID:
        return
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Модель 70b для обработки сложных мульти-запросов
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.5,
            max_tokens=700
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        log_content = (
            f"👤 {message.from_user.first_name} (@{message.from_user.username or 'ID:'+str(message.from_user.id)})\n"
            f"❓ {message.text}\n"
            f"🤖 {response_text[:300]}..." 
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
            bot.reply_to(message, "Связь прервана. Попробуйте снова.")

def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
