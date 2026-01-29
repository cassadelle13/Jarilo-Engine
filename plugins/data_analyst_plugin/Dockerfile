# Dockerfile для Data Analyst Plugin
FROM python:3.11-slim

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скрипта запуска
COPY run.sh .
RUN chmod +x run.sh

# Рабочая директория
WORKDIR /workspace

# Команда по умолчанию - держать контейнер запущенным
CMD ["tail", "-f", "/dev/null"]