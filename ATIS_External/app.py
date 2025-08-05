from flask import Flask, render_template, request
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Index route
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", response=None, sector="", role="", prompt="")

# Generate route
@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Get form input data (not JSON)
        sector = request.form.get("sector")
        role = request.form.get("role")
        prompt = request.form.get("prompt")

        print(f"📥 Received Prompt: {prompt} | Sector: {sector} | Role: {role}")

        # Call OpenAI GPT-4 Turbo
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a Defence Training AI Coach supporting the sector: {sector} and role: {role}. Provide helpful, clear guidance.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        reply = response.choices[0].message.content.strip()
        print(f"🧠 GPT Response: {reply}")

        return render_template("index.html", response=reply, sector=sector, role=role, prompt=prompt)

    except Exception as e:
        error_message = f"❌ Error occurred in /generate route:\n\n{str(e)}"
        print(error_message)
        return render_template("index.html", response=error_message, sector="", role="", prompt="")

# Run the Flask app
if __name__ == "__main__":
    print("🔐 Loaded API Key:", "SET" if OPENAI_API_KEY else "MISSING")
    app.run(debug=True)
