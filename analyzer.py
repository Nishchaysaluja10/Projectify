import os
import requests
import google.generativeai as genai

# 🛑 GLOBAL FLAG: Tracks if Gemini has hit a rate limit during this worker session
gemini_exhausted = False

def analyze_code_chunk(function_name, file_name, code_text):
    global gemini_exhausted
    
    """Attempts to use Gemini first. If quota is exhausted, falls back to local Ollama permanently for this session."""
    
    prompt = f"""
    CRITICAL INSTRUCTION: You MUST end your entire response with a Mermaid.js flowchart. Do not stop generating until the Mermaid block is complete.

    Act as if you are the original architect and core developer of this entire codebase, as well as a highly experienced technical mentor. You know the "heart" of this code intimately, and you possess a gift for teaching complex logic to absolute beginners.

    Analyze the following Python function extracted from `{file_name}`.

    Function Name: {function_name}
    Code:
    {code_text}

    Provide a warm, detailed, and structured educational breakdown of this function using the exact format below. Speak directly to the fresher in the first person ("I built this to...", "Here, we are..."). 

    ### 🌟 The Heart of the Function
    Explain the soul and core purpose of this function in plain, jargon-free English. Imagine you are drawing on a whiteboard for a student. What real-world user action or core business requirement does this specific block handle?

    ### 🛠️ How I Built It (Step-by-Step)
    Walk through the chronological logic point by point. Teach the mechanics clearly. Focus on *why* the code is doing what it does at each major step, rather than just reading back the syntax.

    ### 🔀 Data Flow & Variable Mapping
    Demystify the data for the junior developer. Clearly map out the life-cycle of the critical variables here: 
    * Where is the data originating from? (e.g., Is it coming from a frontend form, URL parameters, a user session, or an API call?)
    * How is it being transformed or validated?
    * What is the final output or payload being returned?

    ### 🔗 Ecosystem Connections
    List the specific dependencies. Which database tables are we querying or updating? Which HTML templates are being rendered? Which other internal modules or functions does this piece rely on to do its job?

    ### 📊 Logic Flowchart
    Create a visual flowchart representing the chronological execution path of this function. 
    Use Mermaid.js syntax with `graph TD`. 
    Focus on conditional branches (if/else), loops, and return states.
    
    CRITICAL MERMAID RULE: If any node text contains spaces, punctuation, or special characters (like parentheses, colons, brackets, or operators like = or >), you MUST wrap the text in double quotes to prevent syntax errors!
    Example Correct: A["Initialize State: (stores = [])"]
    Example Incorrect: A[Initialize State: (stores = [])]
    
    You MUST wrap the diagram code in a standard markdown code block with the language tagged as 'mermaid', like this:
    ```mermaid
    graph TD
        A["Start"] --> B("Process data")
    ```
    """
    
    # ==========================================
    # ROUTE 1: THE CLOUD (Gemini 2.5)
    # ==========================================
    # Only try Gemini if we haven't already exhausted our quota in a previous run
    if not gemini_exhausted:
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                # We add a tag so you know which AI answered in the database
                return f"[☁️ Gemini] {response.text}"
                
            except Exception as e:
                # If we hit a rate limit, flip the global flag to True
                print(f"\n⚠️ Gemini API Failed (Likely rate limit). Disabling Cloud routing for the rest of this batch... Error: {e}")
                gemini_exhausted = True
    
    # ==========================================
    # ROUTE 2: THE FALLBACK (Local Ollama)
    # ==========================================
    # If we get here, either Gemini failed on this specific run, 
    # or it failed earlier and the global flag bypassed Route 1.
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