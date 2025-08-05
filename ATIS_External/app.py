from flask import Flask, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are an AI expert in {sector} sector, acting as a {role}."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': reply})

    except Exception as e:
        print("❌ Error occurred in /generate route:\n")
        print(f"Error code: 400 - {e}")
        return jsonify({'response': 'Error generating response.'}), 400

if __name__ == '__main__':
    app.run(debug=True)
