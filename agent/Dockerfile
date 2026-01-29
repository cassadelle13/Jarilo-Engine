# Используем легковесный базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код агента (пока это будет заглушка,
# которую мы создадим на следующем шаге)
COPY src/ .

# Указываем, какой скрипт запускать при старте контейнера
ENTRYPOINT ["python", "main.py"]