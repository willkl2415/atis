import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
import openai

# ✅ Load .env explicitly from same folder as this script
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# ✅ Load API key and set it
api_key = os.getenv("OPENAI_API_KEY")
print(f"🔐 Loaded API Key: {api_key[:10]}..." if api_key else "❌ API Key NOT LOADED")
openai.api_key = api_key

app = Flask(__name__)

# ✅ Main route
@app.route('/')
def index():
    return render_template('index.html')

# ✅ Prompt submission route
@app.route('/submit', methods=['POST'])
def submit():
    sector = request.form['sector']
    role = request.form['role']
    prompt = request.form['prompt']

    try:
        # GPT inference call
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an AI assistant for the {sector} sector. The user's role is {role}."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        reply = response.choices[0].message.content.strip()
        return render_template('index.html', output=reply, sector=sector, role=role, prompt=prompt)

    except Exception as e:
        return render_template('index.html', output=f"Error: {str(e)}", sector=sector, role=role, prompt=prompt)

if __name__ == '__main__':
    app.run(debug=True)
