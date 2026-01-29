import sqlite3
import sys
sys.path.insert(0, 'src')

conn = sqlite3.connect('src/jarilo_state.db')
cursor = conn.cursor()

try:
    # Создаем таблицы как в моделях
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        priority INTEGER DEFAULT 1,
        workspace_id TEXT,
        user_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        step_id TEXT UNIQUE NOT NULL,
        task_id INTEGER NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        order_num INTEGER,
        result TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    ''')
    
    conn.commit()
    print('✅ Таблицы созданы успешно')
    
    # Проверяем структуру
    cursor.execute('PRAGMA table_info(tasks)')
    columns = cursor.fetchall()
    print('📊 Структура tasks:')
    for column in columns:
        print(f'  - {column[1]} ({column[2]})')
        
except Exception as e:
    print(f'❌ Ошибка: {e}')
finally:
    conn.close()
