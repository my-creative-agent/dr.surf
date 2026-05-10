# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем библиотеки: pyTelegramBotAPI, groq, flask
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код бота
COPY main.py .

# Открываем порт 7860 (стандарт для таких сервисов)
EXPOSE 7860

# Запускаем бота
CMD ["python", "main.py"]
