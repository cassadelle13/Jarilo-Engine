# Dockerfile для сервера Jarilo Brain
FROM python:3.11-slim

# Создание непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash app

# Установка рабочей директории
WORKDIR /app

# Создание директории для БД и установка прав
RUN mkdir -p /app && chown -R app:app /app
RUN mkdir -p /app/data && chown -R app:app /app/data

# Копирование файла зависимостей (для кэширования)
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ .

# Смена пользователя
# USER app

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
