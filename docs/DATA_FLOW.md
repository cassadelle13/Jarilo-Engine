# Потоки данных в Jarilo

## Основные workflow

1. **Генерация workflow**
   - Frontend → POST /api/v1/workflows/generate
   - Brain → LangChain → Результат

2. **Выполнение workflow**
   - Инициализация → Создание контекста
   - Последовательное выполнение нод
   - Обработка ошибок

## Схема хранения данных
```
└── data/
    ├── workflows/  # Конфиги workflow
    ├── state/     # Текущие состояния
    └── artifacts/ # Результаты выполнения
```
