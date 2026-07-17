# worker.py
import os
import subprocess
import tempfile
from celery import Celery
from dotenv import load_dotenv

# Import our new merged logic and database models
from analyzer import process_repository_to_db
from database import db, Repository
# We import the Flask app to give SQLAlchemy the execution context
from app import app as flask_app 

load_dotenv()

# Point this to your local Redis instance
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery('tasks', broker=redis_url)

@celery_app.task
def parse_repository_task(repo_id, repo_url):
    """
    Clones the repo and runs the instant structural mapping.
    Zero AI is called in this worker.
    """
    print(f"[Worker] Received job to map Repo ID {repo_id}: {repo_url}")
    
    with flask_app.app_context():
        repo = Repository.query.get(repo_id)
        if not repo:
            print(f"[Worker] ❌ Repo ID {repo_id} not found in DB.")
            return "Failed: Repo not found"
            
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                print(f"[Worker] Cloning repository...")
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, temp_dir], 
                    check=True, 
                    capture_output=True
                )
                
                print("[Worker] Running high-speed Tree-Sitter parser...")
                # This single function slices the code, maps the edges, and saves to Postgres
                process_repository_to_db(repo_id, temp_dir)
                
                # Update the state machine
                repo.status = 'parsed'
                db.session.commit()
                print(f"[Worker] ✅ Repository completely mapped in milliseconds!")
                return f"Success for {repo_url}"
                
            except Exception as e:
                print(f"[Worker] ❌ Pipeline failed: {e}")
                repo.status = 'failed_parsing'
                db.session.commit()
                return "Failed"