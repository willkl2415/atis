import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai

# Load API Key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        sector = data.get("sector")
        role = data.get("role")

        # Combine all user inputs
        full_prompt = f"Sector: {sector}\nRole: {role}\nPrompt: {prompt}"

        # Use the new v1 format
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert AI assistant helping with defence training and coaching."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"response": reply})

    except Exception as e:
        print(f"❌ Error occurred in /generate route:\n\n{e}\n")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
