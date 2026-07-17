import requests
import time

# Replace with the actual endpoint you built for the frontend "click"
# and a valid node ID from your DBeaver project_nodes table
NODE_ID = 75
URL = f"http://127.0.0.1:5001/api/node-summary/{NODE_ID}"

print("🖱️  Simulating first click (Should trigger Ollama)...")
start_time = time.time()
response_1 = requests.get(URL)
end_time = time.time()

if response_1.status_code == 200:
    print(f"✅ First Response Time: {end_time - start_time:.2f} seconds")
    print(f"📄 Summary: {response_1.json().get('summary')}")
else:
    print(f"❌ Failed: {response_1.text}")

print("\n" + "-"*40 + "\n")

print("🖱️  Simulating second click (Should hit Redis Cache)...")
start_time = time.time()
response_2 = requests.get(URL)
end_time = time.time()

if response_2.status_code == 200:
    print(f"⚡ Second Response Time: {end_time - start_time:.4f} seconds")
    if (end_time - start_time) < 0.1:
        print("✅ Redis Cache is working perfectly!")
else:
    print(f"❌ Failed: {response_2.text}")