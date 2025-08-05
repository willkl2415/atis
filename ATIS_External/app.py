import os
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print(f"🔐 Loaded API Key: {'set' if api_key else 'not set'}")

# Setup OpenAI API key
openai.api_key = api_key

# Create Flask app
app = Flask(__name__)

# Root route
@app.route('/')
def index():
    return render_template('index.html')

# Handle prompt submission from the frontend
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        role = data.get("role", "")
        sector = data.get("sector", "")

        # Generate response from OpenAI
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
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
