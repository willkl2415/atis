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
