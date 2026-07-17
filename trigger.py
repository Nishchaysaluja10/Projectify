# trigger.py
import requests
import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

github_url = os.getenv("GITHUB_URL")

# The payload simulating what your outside backend will send
payload = {
    "github_url": "https://github.com/nishchaysaluja10/projectify"
}

url = "http://127.0.0.1:5001/api/repositories"

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    data = response.json()
    print("✅ Success!")
    print(f"Response: {data}")
    print("The Celery worker is now parsing it in the background.")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to trigger API: {e}")