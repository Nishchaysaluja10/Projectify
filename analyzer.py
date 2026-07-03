import os
import requests
import google.generativeai as genai

def analyze_code_chunk(function_name, file_name, code_text):
    """Attempts to use Gemini first, then falls back to local Ollama if quota is exhausted."""
    
    prompt = f"""
    You are an expert software architect. Analyze the following Python function extracted from `{file_name}`.
    
    Function Name: {function_name}
    Code:
    {code_text}
    
    Provide a concise, 2-sentence summary of what this specific function does and what database tables or other modules it appears to interact with.
    """
    
    # ==========================================
    # ROUTE 1: THE CLOUD (Gemini 2.5)
    # ==========================================
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            # We add a tag so you know which AI answered in the database
            return f"[☁️ Gemini] {response.text}"
            
        except Exception as e:
            # If we hit a rate limit, we print a warning and let the code continue to Route 2
            print(f"\n⚠️ Gemini API Failed (Likely rate limit). Redirecting to local model... Error: {e}")
    
    # ==========================================
    # ROUTE 2: THE FALLBACK (Local Ollama)
    # ==========================================
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return f"[💻 Local] {result.get('response', 'No response generated.')}"
        
    except Exception as e:
        return f"❌ CRITICAL: Both Cloud and Local AI Analysis Failed: {e}"