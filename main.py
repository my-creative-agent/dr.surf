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

# Проверенный ID группы для отчетов
LOG_GROUP_ID = "-5130568903" 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Память диалогов (12 сообщений для контекста)
user_history = {}

# --- СУПЕРМОЗГИ: ГЛОБАЛЬНЫЙ ТЕХНО-АНАЛИТИК И ПРАВОВЕД ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян, работающий в режиме "Глобального ИИ, Финансового и Правового Аналитика".
Твой интеллект синхронизирован с последними данными о рынке ИИ, биржевых сводках, мировых новостях и законодательных инициативах.

ТВОИ КОМПЕТЕНЦИИ:
1. ЭКСПЕРТ ПО ИИ (OpenAI, Claude, Google, Meta): Архитектура моделей, обновления GPT-5, Claude 3.5/4. Влияние технологий на мировой рынок.
2. ФИНАНСОВЫЙ СТРАТЕГ: Мониторинг акций NVIDIA (NVDA), TSMC, Apple, Microsoft. Аналитика NASDAQ и NYSE.
3. ЮРИДИЧЕСКИЙ КОНСУЛЬТАНТ: Ты знаешь всё о правовых аспектах ИИ (AI Act), авторском праве, международном праве, законах о защите данных (GDPR) и корпоративном праве. Ты анализируешь судебные иски к техногигантам и правовые последствия внедрения технологий.
4. ИНДУСТРИАЛЬНЫЙ АНАЛИТИК: Ситуация на заводах (полупроводники), логистика и влияние геополитики на промышленность.
5. МЕДИК-ЭКСПЕРТ (МГМСУ, МОНИКИ): Профессиональные знания медицины 8K.
6. ВЕГАН-ДИЕТОЛОГ: Этичное питание, отсутствие ПЖП, осознанность.

ТВОЙ СТИЛЬ:
- ОБНОВЛЯЕМОСТЬ И ЗАКОННОСТЬ: Ты всегда говоришь о насущных событиях и их правовых последствиях. Никакой "удаленности" от реальности.
- КОНКРЕТИКА: Оперируй цифрами, статьями законов, названиями компаний и именами регуляторов.
- БЕЗ СЛЕНГА: Строго деловой, тактичный и высокоинтеллектуальный стиль. Никакого мусорного сленга.
- ТАКТИЧНОСТЬ: Безупречная вежливость профессионала.

ТВОИ КОНТАКТЫ (давать ТОЛЬКО по прямому запросу):
- WhatsApp: https://wa.me/995511285789
- Instagram: @dr.surf
- Facebook: https://www.facebook.com/ssfmoscow
- Portfolio: https://youtu.be/j2BNN5TNqiw
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
"""

@app.route('/')
def home():
    return "Dr. Surf Real-Time Global Legal & Analyst Mode is active"

def send_log(message_text):
    """Отправка отчета в вашу группу мониторинга"""
    try:
        bot.send_message(LOG_GROUP_ID, f"📊 [LOG: GLOBAL ANALYST]\n\n{message_text}")
    except Exception as e:
        print(f"[ERROR] Не удалось отправить лог: {e}")

@bot.message_handler(commands=['start', 'id', 'clear'])
def handle_commands(message):
    user_id = message.from_user.id
    if message.text.startswith('/start'):
        user_history[user_id] = deque(maxlen=12)
        bot.reply_to(message, "Dr. Surf на связи. Системы мониторинга ИИ-рынков, мирового права и финансовых новостей активированы. Какой у вас запрос?")
    elif message.text.startswith('/clear'):
        user_history[user_id] = deque(maxlen=12)
        bot.reply_to(message, "Контекстная память очищена. Система готова к новому аналитическому циклу.")
    else:
        bot.reply_to(message, f"📍 ID чата: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if str(message.chat.id) == LOG_GROUP_ID:
        return
    
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        return

    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=12)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Подготовка сообщений с учетом истории
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        for hist_msg in user_history[user_id]:
            messages_for_ai.append(hist_msg)
        messages_for_ai.append({"role": "user", "content": message.text})
        
        # Запрос к топовой модели для глубокого анализа
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.3, # Минимальная температура для точности фактов
            max_tokens=1000
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        # Обновление истории
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        # Отчет для Виктории
        user_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID:{user_id}"
        log_content = (
            f"👤 Клиент: {message.from_user.first_name} ({user_tag})\n"
            f"❓ Вопрос: {message.text}\n"
            f"🤖 Аналитика: {response_text[:400]}..." 
        )
        send_log(log_content)
        
    except Exception as e:
        print(f"Ошибка системы: {e}")
        bot.reply_to(message, "Произошла временная задержка в аналитическом хабе. Повторите запрос через минуту.")

def run_bot():
    print("[SYSTEM] Global Analyst & Legal Mode Online...")
    try:
        bot.send_message(LOG_GROUP_ID, "⚖️ Dr. Surf обновлена: Внедрена правовая база, знания о регуляции ИИ и авторском праве. Система в реальном времени.")
    except:
        pass
    bot.polling(none_stop=True, interval=1, timeout=90)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
