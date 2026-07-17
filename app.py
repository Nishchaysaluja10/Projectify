import os
import requests
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db, Repository, ProjectNode

app = Flask(__name__)
CORS(app)
# -------------------------------------------------------------------
# 1. PostgreSQL Database Configuration
# -------------------------------------------------------------------
# Replace with your actual PostgreSQL credentials
# app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Messi_10@localhost:5432/projectify_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# -------------------------------------------------------------------
# 2. Redis Cache Configuration
# -------------------------------------------------------------------
# decode_responses=True ensures we get clean strings back, not raw bytes
cache = redis.Redis(
    host='localhost', 
    port=6379, 
    db=0, 
    decode_responses=True
)

# -------------------------------------------------------------------
# API Routes
# -------------------------------------------------------------------

@app.route('/api/repositories', methods=['POST'])
def ingest_repository():
    """
    Endpoint for your external backend to push a GitHub link here.
    Registers the repo and triggers the background tree-sitter parser.
    """
    data = request.json
    github_url = data.get('github_url')
    
    if not github_url:
        return jsonify({"error": "github_url is required"}), 400
        
    # Check if already exists
    existing_repo = Repository.query.filter_by(github_url=github_url).first()
    if existing_repo:
        # Trigger Celery task even if it already exists, or maybe not? 
        # Actually let's queue it so the background worker parses it if not done.
        from worker import parse_repository_task
        parse_repository_task.delay(existing_repo.id, github_url)
        return jsonify({"message": "Repository already exists and queued for parsing", "repo_id": existing_repo.id}), 200

    new_repo = Repository(github_url=github_url)
    db.session.add(new_repo)
    db.session.commit()
    
    # Push to Celery queue here to trigger git clone & tree-sitter parsing
    from worker import parse_repository_task
    parse_repository_task.delay(new_repo.id, github_url)
    
    return jsonify({"message": "Repository ingested and queued for parsing", "repo_id": new_repo.id}), 201

@app.route('/api/repositories/<int:repo_id>/nodes', methods=['GET'])
def get_repository_map(repo_id):
    """
    Returns the complete structural map of the repository so the Vue frontend 
    can draw the visual nodes and edges instantly.
    """
    nodes = ProjectNode.query.filter_by(repository_id=repo_id).all()
    
    map_data = []
    for node in nodes:
        map_data.append({
            "id": node.id,
            "node_name": node.node_name,
            "node_type": node.node_type,
            "edges": node.structural_metadata # Returns the JSONB inbound/outbound links
        })
        
    return jsonify({"repository_id": repo_id, "nodes": map_data}), 200

@app.route('/api/node-summary/<int:node_id>', methods=['GET'])
def get_node_summary(node_id):
    """
    The Lazy-Loading engine. Checks Redis first, falls back to Ollama.
    """
    cache_key = f"node_summary:{node_id}"
    
    # 1. Check RAM Cache (~1ms latency)
    cached_summary = cache.get(cache_key)
    if cached_summary:
        return jsonify({"summary": cached_summary, "source": "redis_cache"}), 200
        
    # 2. Cache Miss: Fetch Node from PostgreSQL
    node = ProjectNode.query.get_or_404(node_id)
    
    # Extract contextual edges from the JSONB column to feed the LLM
    metadata = node.structural_metadata or {}
    inbound_calls = metadata.get("inbound_calls", [])
    outbound_calls = metadata.get("outbound_calls", [])
    
    # 3. Construct the Token-Optimized Prompt
    prompt = f"""
    System: You are a codebase teaching assistant. Explain this code block to a student. Output strictly a 2-sentence explanation. No markdown, no introductions.
    Code: {node.code_content}
    This block is CALLED BY: {inbound_calls}
    This block CALLS: {outbound_calls}
    
    Provide a concise 2-sentence explanation:
    1. What this code block handles internally.
    2. How it bridges its callers to its dependencies.
    """
    
    try:
        # 4. Query local Ollama instance
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": "qwen2.5-coder:1.5b", # Fast, low-parameter model
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,
                "num_predict": 150 # Hard cap on token generation
            }
        }, timeout=10)
        
        response.raise_for_status()
        generated_summary = response.json().get('response', '').strip()
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to generate summary via Ollama", "details": str(e)}), 500

    # 5. Store in Redis for 24 hours (86400 seconds)
    cache.setex(cache_key, 86400, generated_summary)
    
    return jsonify({"summary": generated_summary, "source": "ollama_generation"}), 200

if __name__ == '__main__':
    # Create tables if they don't exist (useful for initial local setup)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)