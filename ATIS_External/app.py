from flask import Flask, request, render_template
from dotenv import dotenv_values
from pathlib import Path
import openai
import os

# Setup Flask app
app = Flask(__name__)

# Load .env from ATIS root folder (one level up from this file)
env_path = Path(__file__).resolve().parent.parent / ".env"
config = dotenv_values(env_path)
openai.api_key = config.get("OPENAI_API_KEY")

# Debug: confirm API key loaded
print("🔐 Loaded API Key:", openai.api_key)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Form submission route
@app.route('/submit', methods=['POST'])
def submit():
    try:
        sector = request.form['sector']
        role = request.form['role']
        prompt = request.form['prompt']

        full_prompt = f"""You are an AI Assistant helping a user in the {sector} sector with the role of {role}.
They have submitted the following request:

"{prompt}"

Please respond with helpful, contextually relevant guidance."""

        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "You are a helpful AI coach for professional training guidance."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.5,
            max_tokens=800
        )

        output = response.choices[0].message['content']
        return render_template('index.html', response=output)

    except Exception as e:
        return render_template('index.html', response=f"Error: {str(e)}")

# Run app
if __name__ == '__main__':
    app.run(debug=True)
