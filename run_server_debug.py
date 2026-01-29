"""
Запуск сервера с расширенным логированием для отладки.
"""
import sys
import os
import logging

# Установка уровня логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Добавление пути
sys.path.insert(0, os.path.abspath("brain/src"))

print("Запуск FastAPI приложения с расширенным логированием...")
print("=" * 60)

# Импортируем FastAPI приложение
from main import app

if __name__ == "__main__":
    import uvicorn
    import traceback
    
    print("Конфигурация:")
    print(f"  Хост: 127.0.0.1")
    print(f"  Порт: 8004")
    print(f"  Логирование: DEBUG")
    print("=" * 60)
    
    try:
        uvicorn.run("main:app", host="127.0.0.1", port=8004, log_level="debug")
    except Exception as e:
        print("ОШИБКА: Сервер завершился с исключением!")
        print(f"Тип исключения: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        print("Полный traceback:")
        traceback.print_exc()
