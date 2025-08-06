from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file.")

# Create OpenAI client using new v1+ syntax
client = OpenAI(api_key=api_key)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()

        prompt = data.get("prompt", "").strip()
        sector = data.get("sector", "").strip()
        role = data.get("role", "").strip()

        print(f"📥 Received Prompt: {prompt} | Sector: {sector} | Role: {role}")

        if not prompt:
            return jsonify({'response': 'Prompt is required.'}), 400

        system_msg = f"You are an AI assistant in the {sector} sector, acting as a {role}."
        user_msg = prompt

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
        )

        result = completion.choices[0].message.content.strip()
        return jsonify({'response': result})

    except OpenAIError as oe:
        print("❌ OpenAI API Error:", oe)
        return jsonify({'response': 'OpenAI API error occurred.'}), 500

    except Exception as e:
        print("❌ General Error in /generate:", e)
        return jsonify({'response': 'Internal server error occurred.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
