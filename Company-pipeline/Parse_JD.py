import os
import json
import PyPDF2
from google import genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# The new SDK automatically picks up GEMINI_API_KEY from your .env file
client = genai.Client()

# A health check so the browser doesn't throw a 404 on the base URL
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ProjectHire API is running. Send a POST request with a PDF to /api/company/parse-jd"}), 200

@app.route('/api/company/parse-jd', methods=['POST'])
def parse_jd_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        pdf_reader = PyPDF2.PdfReader(file)
        raw_jd_text = ""
        for page in pdf_reader.pages:
            raw_jd_text += page.extract_text() + "\n"

        prompt = f"""
        You are an expert technical recruiter and engineering manager. 
        Analyze the following Job Description and extract the requirements into a strict JSON object.
        Do not include any markdown formatting, backticks, or conversational text. Return ONLY valid JSON.

        Required JSON Structure:
        {{
            "job_title": "Extracted title",
            "experience_level": "Junior, Mid, Senior, or Lead",
            "core_stack": ["List", "of", "languages", "and", "frameworks"],
            "infrastructure_requirements": ["List", "of", "devops", "cloud", "or", "db", "tools"],
            "required_features": ["3 to 5 high-level features the candidate will likely build, e.g., 'User Auth', 'Payment Pipelines'"],
            "project_matching_rubric": {{
                "look_for_architecture": "1 sentence describing the ideal architecture style",
                "look_for_complexity": "1 sentence describing what complex logic to look for in a candidate's codebase",
                "dealbreakers": "1 sentence describing what missing skills or poor practices would disqualify them"
            }},
            "recommended_interview_focus": "1 sentence suggesting what to ask in the technical interview"
        }}

        Job Description Text:
        {raw_jd_text}
        """

        # Call the new GenAI SDK
        response = client.models.generate_content(
            model='gemini-3.7-flash',
            contents=prompt
        )
        
        cleaned_response = response.text.replace('```json', '').replace('```', '').strip()
        parsed_jd_data = json.loads(cleaned_response)

        return jsonify({
            "success": True,
            "parsed_data": parsed_jd_data
        }), 200

    except json.JSONDecodeError:
        return jsonify({"error": "LLM failed to return valid JSON. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)