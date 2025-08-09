from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import openai

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    sector = data.get("sector", "")
    func   = data.get("func", "")
    role   = data.get("role", "")
    prompt = data.get("prompt", "")

    full_prompt = (
        f"You are an expert in {sector}, working within the function '{func}', acting as a {role}. "
        f"Answer concisely and practically. Question: {prompt}"
    )

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a fast, helpful performance support assistant."},
                {"role":"user","content": full_prompt}
            ],
            max_tokens=450,
            temperature=0.2,
        )
        return {"response": resp.choices[0].message["content"].strip()}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
