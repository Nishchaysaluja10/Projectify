import sqlite3
import pandas as pd

def view_architecture_map():
    # Connect to the SQLite database
    conn = sqlite3.connect('architecture_map.db')
    
    # Read the data into a Pandas DataFrame
    try:
        df = pd.read_sql_query("SELECT file_name, function_code, ai_summary FROM functions", conn)
        
        print("\n" + "="*70)
        print("🧠 AI ARCHITECTURE MAP EXTRACTED")
        print("="*70)
        
        for index, row in df.iterrows():
            print(f"\n📍 File: {row['file_name']}")
            print("💻 Code:")
            print(row['function_code'])
            print(f"\n💡 AI Analysis: {row['ai_summary']}")
            print("-" * 70)
            
    except Exception as e:
        print(f"Error reading database: {e}")
        
    conn.close()

if __name__ == "__main__":
    view_architecture_map()