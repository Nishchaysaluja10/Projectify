import os
import sys 
import subprocess
import tempfile
from celery import Celery
from dotenv import load_dotenv

# Import our custom microservice modules
from slicer import extract_python_functions
from analyzer import analyze_code_chunk
from database import init_db, save_to_db

current_directory = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(current_directory, '.env')
load_dotenv(env_file_path)

redis_url = os.getenv("UPSTASH_REDIS_URL")

if not redis_url:
    print("FATAL ERROR: Could not find UPSTASH_REDIS_URL.")
    sys.exit(1)

# Boot up the database before the worker starts listening
init_db()

app = Celery('tasks', broker=redis_url)

@app.task
def process_repository(repo_url):
    print(f"[Worker] Received job to map: {repo_url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print(f"[Worker] Cloning repository...")
            subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
            
            print("[Worker] Slicing codebase...")
            functions = extract_python_functions(temp_dir)
            
            if functions:
                print(f"[Worker] 🧠 Analyzing and storing ALL {len(functions)} functions...")
                
                # Loop through absolutely every single function found across all files
                for i in range(len(functions)):
                    file_name = functions[i]['file']
                    code = functions[i]['code']
                    
                    # 1. Ask the Hybrid Analyzer for the summary
                    ai_summary = analyze_code_chunk("Extracted_Function", file_name, code)
                    
                    # 2. Save everything permanently to the database
                    save_to_db(repo_url, file_name, code, ai_summary)
                    
                    print(f"✅ [{i+1}/{len(functions)}] Saved {file_name} chunk to database.")
            
            return f"Processed {len(functions)} functions"

        except subprocess.CalledProcessError as e:
            print(f"[Worker] Clone failed: {e}")
            return "Failed"