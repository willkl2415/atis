from flask import Flask, render_template, request, jsonify
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file.")

# Set OpenAI key using new v1.0+ method
openai_client = openai.OpenAI(api_key=api_key)

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

        # Create chat response
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are an AI assistant in the {sector} sector, performing the role of a {role}."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({'response': reply})

    except Exception as e:
        print("❌ Error occurred in /generate route:")
        print(e)
        return jsonify({'response': 'Error generating response.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
