# PowerShell Script: setup-atis-external.ps1
# This script sets up the ATIS External fork with a Flask backend and GPT-4 Turbo integration

# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install required Python packages
pip install flask openai flask-cors python-dotenv

# 3. Write app.py
@"
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

@app.route("/generate", methods=["POST"])
def generate_response():
    data = request.get_json()
    sector = data.get("sector", "")
    role = data.get("role", "")
    user_prompt = data.get("prompt", "")

    if not user_prompt.strip():
        return jsonify({"response": "Nothing found. Please rephrase or rewrite your prompt."})

    full_prompt = (
        f"You are an AI assistant working within the '{sector}' sector as a '{role}'. "
        f"Respond professionally and clearly to the following user prompt:\n\n{user_prompt}"
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert AI assistant trained to give sector-specific and role-appropriate answers."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        gpt_output = completion.choices[0].message.content.strip()
        return jsonify({"response": gpt_output})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
"@ | Out-File -Encoding UTF8 app.py

# 4. Write index.html
@"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ATIS External - AI Coaching Interface</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f4f4f4;
        }
        h1 {
            color: #333;
        }
        label {
            font-weight: bold;
            display: block;
            margin-top: 20px;
        }
        select, textarea, button {
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            font-size: 16px;
        }
        #responseBox {
            background-color: #e8f0fe;
            border-left: 6px solid #4285f4;
            padding: 20px;
            margin-top: 30px;
            white-space: pre-wrap;
            min-height: 100px;
        }
    </style>
</head>
<body>
    <h1>ATIS External (GPT-4 Turbo Powered)</h1>

    <label for="sector">Select Sector:</label>
    <select id="sector">
        <option>Defence (Training)</option>
        <option>Education</option>
        <option>Healthcare</option>
        <option>Engineering</option>
        <option>Retail</option>
        <option>Finance</option>
        <option>Government</option>
        <option>Technology</option>
    </select>

    <label for="role">Select Role:</label>
    <select id="role">
        <option>Training Analyst</option>
        <option>Training Designer</option>
        <option>Content Developer</option>
        <option>Team Leader</option>
        <option>Project Manager</option>
        <option>HR Manager</option>
        <option>Learning Consultant</option>
        <option>Systems Engineer</option>
    </select>

    <label for="prompt">Enter your prompt:</label>
    <textarea id="prompt" rows="6" placeholder="Type your question or task here..."></textarea>

    <button onclick="submitPrompt()">Submit</button>

    <div id="responseBox">Your response will appear here.</div>

    <script>
        async function submitPrompt() {
            const sector = document.getElementById("sector").value;
            const role = document.getElementById("role").value;
            const prompt = document.getElementById("prompt").value.trim();
            const responseBox = document.getElementById("responseBox");

            if (!prompt) {
                responseBox.textContent = "Please enter a prompt.";
                return;
            }

            responseBox.textContent = "Thinking...";

            try {
                const res = await fetch("http://127.0.0.1:5000/generate", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ sector, role, prompt })
                });

                const data = await res.json();
                responseBox.textContent = data.response || "No response received.";
            } catch (error) {
                responseBox.textContent = "Error contacting the server. Please ensure the Flask backend is running.";
            }
        }
    </script>
</body>
</html>
"@ | Out-File -Encoding UTF8 index.html

# 5. Write .env file with placeholder
@"
OPENAI_API_KEY=sk-your-real-api-key-here
"@ | Out-File -Encoding UTF8 .env

# 6. Done
Write-Host "`n✅ ATIS External setup complete. Now run the backend:"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   python app.py"
Write-Host "`nThen open index.html in your browser to start using GPT-4 Turbo."
