import sqlite3

def init_db():
    """Creates the database and the required table if they don't exist."""
    conn = sqlite3.connect('architecture_map.db')
    cursor = conn.cursor()
    
    # Create a table to store our AI-analyzed functions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repository_url TEXT,
            file_name TEXT,
            function_code TEXT,
            ai_summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(repo_url, file_name, code, ai_summary):
    """Inserts a processed function into the database."""
    conn = sqlite3.connect('architecture_map.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO functions (repository_url, file_name, function_code, ai_summary)
        VALUES (?, ?, ?, ?)
    ''', (repo_url, file_name, code, ai_summary))
    
    conn.commit()
    conn.close()