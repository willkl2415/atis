import os
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

print(f"🔐 Loaded API Key: {'SET' if api_key else 'NOT SET'}")

openai.api_key = api_key

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        role = data.get("role", "")
        sector = data.get("sector", "")

        if not api_key:
            raise ValueError("API key not found or not loaded.")

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": f"You are an expert assistant for someone working in the {sector} sector as a {role}."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response['choices'][0]['message']['content']
        return jsonify({"response": reply})

    except Exception as e:
        print("❌ Error occurred in /generate route:")
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
