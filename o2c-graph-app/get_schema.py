import sqlite3

def write_schema():
    conn = sqlite3.connect('D:\\Dodge\\o2c-graph-app\\o2c.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open('D:\\Dodge\\o2c-graph-app\\schema.txt', 'w', encoding='utf-8') as f:
        for table in tables:
            table_name = table[0]
            f.write(f"Table: {table_name}\n")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                f.write(f"  - {col[1]} ({col[2]})\n")
            f.write("\n")

if __name__ == "__main__":
    write_schema()
