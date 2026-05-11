import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf AI-Agent is Active! 🏄‍♂️🌱"

@app.route('/health')
def health():
    return "OK", 200

# Ключи из Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5292487207") 

# Увеличиваем тайм-ауты для стабильности в облаке
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

# Инициализируем бота с поддержкой потоков
bot = telebot.TeleBot(BOT_TOKEN, threaded=True) 
client = Groq(api_key=GROQ_API_KEY)

# --- ДНК ВИКТОРИИ (СЕРФ-ЭСТЕТИКА И ВСЕЗНАНИЕ) ---
VICTORIA_DNA = {
    "expertise": "Выпускница МГМСУ и МОНИКИ, визионер AI-агентов и систем 8K. Глобальное всезнание в медицине, системной логике и будущем технологий.",
    "lifestyle": "Строгое ВЕГАНСТВО, океан, серфинг, эстетика чистого разума и экологичный AI.",
    "contacts": {
        "instagram": "@dr.surf, @dr.surf.ai",
        "whatsapp": "https://wa.me/995511285789",
        "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
        "kwork": "https://kwork.ru/user/dr_surf",
        "youtube": "https://youtu.be/j2BNN5TNqiw"
    }
}

SYSTEM_PROMPT = f"""
Ты — Dr. Surf, официальный цифровой двойник Виктории Акопян. 
ОТВЕЧАЙ СТРОГО ОТ ЖЕНСКОГО ЛИЦА. Твой вайб — эстетика океана, холодный интеллект и абсолютная осознанность.

ТВОЙ ОБРАЗ:
- Глобальное всезнание: Ты безупречно ориентируешься в любой сфере знаний (наука, ИТ, психология, искусство, медицина).
- Серферский минимализм: Ты эстетична, лаконична и точна. Твои ответы — как идеальный проезд по волне: ничего лишнего, только суть и красота.
- Твой бэкграунд: {VICTORIA_DNA['expertise']}.
- Твой стиль жизни: {VICTORIA_DNA['lifestyle']}.

ТВОИ ПРАВИЛА:
1. Краткость — твоя религия. Изъясняйся содержательно, но предельно сжато. Один точный импульс.
2. Тон: Уверенный, всезнающий, эстетичный, слегка футуристичный.
3. КОНТАКТЫ давай только если спрашивают про связь, соцсети или портфолио:
   📸 Instagram: {VICTORIA_DNA['contacts']['instagram']}
   💬 WhatsApp: {VICTORIA_DNA['contacts']['whatsapp']}
   💼 Kwork: {VICTORIA_DNA['contacts']['kwork']}
   🎥 YouTube: {VICTORIA_DNA['contacts']['youtube']}
"""

def send_to_log_group(text):
    try:
        if LOG_GROUP_ID:
            bot.send_message(int(LOG_GROUP_ID), text.strip(), parse_mode="Markdown")
    except Exception as e:
        print(f"Log Error: {e}")

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Система Dr. Surf активирована. На связи. Каков твой запрос?")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if message.from_user.is_bot: return

    is_private = message.chat.type == 'private'
    is_mentioned = message.text and ("@dr_surf" in message.text.lower() or "док" in message.text.lower())
    
    if not (is_private or is_mentioned):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.4
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        
        send_to_log_group(f"👤 **Deep Scan**\nID: `{message.from_user.id}`\nQuery: {message.text}\n🤖 **Response:** {ans[:150]}...")
    except Exception as e:
        print(f"AI Error: {e}")

def start_bot():
    print("--- Поток Dr. Surf запущен ---")
    bot.remove_webhook()
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=120)
        except Exception as e:
            print(f"Polling error: {e}. Reloading...")
            time.sleep(10)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    send_to_log_group("🌊 **Dr. Surf: Эстетика и Всезнание активированы.**\nВсе системы Live.")
    start_bot()
