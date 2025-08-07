from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import openai
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    sector = data.get("sector", "")
    role = data.get("role", "")
    prompt = data.get("prompt", "")

    full_prompt = f"You are an expert in {sector}, acting as a {role}. {prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return {"response": response.choices[0].message["content"].strip()}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}