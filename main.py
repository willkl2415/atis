from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os, openai

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM = "You are a concise, practical performance coach. Keep answers clear and immediately useful."

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    sector = data.get("sector", "")
    func   = data.get("func", "")
    role   = data.get("role", "")
    prompt = data.get("prompt", "")

    full_prompt = f"Sector: {sector}\nFunction: {func}\nRole: {role}\nUser question: {prompt}"

    try:
      resp = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[{"role":"system","content":SYSTEM},
                    {"role":"user","content":full_prompt}],
          max_tokens=500, temperature=0.5,
        )
      text = resp.choices[0].message["content"].strip()
      return {"response": text}
    except Exception as e:
      return {"response": f"Error: {e}"}
