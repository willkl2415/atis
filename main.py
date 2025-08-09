from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import openai

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
    func = data.get("func", "")
    role = data.get("role", "")
    prompt = data.get("prompt", "")

    if not (sector and func and role and prompt):
        return {"response": "Please provide sector, function, role, and a prompt."}

    system = "You are a concise, practical coach that answers clearly without markdown."
    user = (
        f"You are an expert in {sector}, working in the function '{func}', acting as a '{role}'. "
        f"Answer the following as immediate performance support:\n\n{prompt}"
    )

    try:
        # Fast model + short cap for low latency
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            max_tokens=500,
            temperature=0.4,
        )
        text = resp.choices[0].message["content"].strip()
        return {"response": text}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
