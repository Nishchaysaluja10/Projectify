from worker import process_repository
import os

print("Sending Placement Portal job to Redis conveyor belt...")

# We send your actual repo to the background queue
result = process_repository.delay(os.getenv("GITHUB_URL"))

print(f"Job sent! Task ID: {result.id}")