#!/usr/bin/env python3
"""
Прямая инициализация базы данных с правильной схемой
"""

import asyncio
import sys
import sqlite3
from pathlib import Path

# Добавляем src в Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def init_database():
    """Инициализация базы данных с правильной схемой"""
    
    # Удаляем старую базу если существует
    db_path = src_path / "jarilo_state.db"
    if db_path.exists():
        db_path.unlink()
        print("🗑️ Удалена старая база данных")
    
    # Создаем новую базу с правильной схемой
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Создаем таблицу users
        cursor.execute('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # Создаем таблицу tasks с user_id
        cursor.execute('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            workspace_id TEXT,
            user_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # Создаем таблицу steps
        cursor.execute('''
        CREATE TABLE steps (
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
        
        # Создаем таблицу api_keys
        cursor.execute('''
        CREATE TABLE api_keys (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Создаем таблицу secrets
        cursor.execute('''
        CREATE TABLE secrets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            key TEXT NOT NULL,
            encrypted_value TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        print("✅ База данных создана с правильной схемой")
        
        # Проверяем структуру
        cursor.execute('PRAGMA table_info(tasks)')
        columns = cursor.fetchall()
        print("📊 Структура таблицы tasks:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
            
    except Exception as e:
        print(f"❌ Ошибка при создании базы: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(init_database())
