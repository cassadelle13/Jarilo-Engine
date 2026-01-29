import sqlite3

conn = sqlite3.connect('src/jarilo_state.db')
cursor = conn.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)

if tables:
    cursor.execute('PRAGMA table_info(tasks)')
    columns = cursor.fetchall()
    print('Tasks columns:', columns)

conn.close()
