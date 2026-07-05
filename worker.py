import os
import sys 
import subprocess
import tempfile
from celery import Celery
from dotenv import load_dotenv

# Import our custom microservice modules
from slicer import extract_all_functions
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


# ==========================================
# TASK 1: The Master Task (Fast)
# ==========================================
@app.task
def process_repository(repo_url):
    """Clones the repo, slices the functions, and delegates the heavy lifting."""
    print(f"[Master Worker] Received job to map: {repo_url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print(f"[Master Worker] Cloning repository...")
            subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
            
            print("[Master Worker] Slicing codebase...")
            functions = extract_all_functions(temp_dir)
            
            if functions:
                print(f"[Master Worker] Found {len(functions)} functions. Dispatching sub-tasks...")
                
                for i in range(len(functions)):
                    file_name = functions[i]['file_name']
                    # 🟢 FIXED: Grab the file_type from the slicer dictionary
                    file_type = functions[i]['file_type'] 
                    function_name = functions[i]['function_name'] 
                    code = functions[i]['function_code']
                    
                    # 🟢 FIXED: Pass file_type into the delay function
                    analyze_and_save_function.delay(repo_url, file_name, file_type, function_name, code)
                    
            return f"Successfully dispatched {len(functions)} functions to the queue."

        except subprocess.CalledProcessError as e:
            print(f"[Master Worker] Clone failed: {e}")
            return "Failed"


# ==========================================
# TASK 2: The Sub-Task (Heavy)
# ==========================================
@app.task
# 🟢 FIXED: Added file_type as an expected parameter
def analyze_and_save_function(repo_url, file_name, file_type, function_name, code):
    """Handles the AI analysis and database storage for a single function."""
    print(f"[Sub-Worker] 🧠 Analyzing: {file_name} -> {function_name}()")
    
    try:
        # 1. Ask the Hybrid Analyzer for the summary
        ai_summary = analyze_code_chunk(function_name, file_name, code)
        
        # 2. Save everything permanently to the database (including file_type)
        # 🟢 FIXED: Passed file_type to save_to_db to match your new database schema
        save_to_db(repo_url, file_name, file_type, function_name, code, ai_summary)
        
        print(f"✅ Saved {function_name}() to database.")
        return f"Completed {function_name}"
        
    except Exception as e:
        print(f"❌ Failed to process {function_name}(): {e}")
        return f"Failed {function_name}"