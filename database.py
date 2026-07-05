import sqlite3

def init_db():
    conn = sqlite3.connect('architecture_map.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT,
            file_name TEXT,
            file_type TEXT,        -- NEW: python, vue, sql, config
            function_name TEXT, 
            function_code TEXT,
            ai_summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ✅ FIXED: Added file_type as a parameter to match the table schema
def save_to_db(repo_url, file_name, file_type, function_name, function_code, ai_summary):
    conn = sqlite3.connect('architecture_map.db')
    cursor = conn.cursor()
    
    # ✅ FIXED: Updated INSERT statement to include file_type
    cursor.execute('''
        INSERT INTO functions (repo_url, file_name, file_type, function_name, function_code, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (repo_url, file_name, file_type, function_name, function_code, ai_summary))
    
    conn.commit()
    conn.close()