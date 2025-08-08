from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
import asyncio

# --- FastAPI setup ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- OpenAI setup ---
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM = "You are a concise, helpful performance support assistant. Prefer clear, direct guidance."

@app.post("/generate")
async def generate(req: Request):
    try:
        body = await req.json()
        sector = (body.get("sector") or "").strip()
        role = (body.get("role") or "").strip()
        prompt = (body.get("prompt") or "").strip()

        if not prompt:
            return {"response": "Please provide a question."}

        # Keep fast & cheap by default; tune as needed.
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": f"Context: Sector={sector}; Role={role}\n\nQuestion: {prompt}"},
                ],
                max_tokens=400,
                temperature=0.3,
            )
        )
        text = resp.choices[0].message["content"].strip()
        return {"response": text}
    except Exception as e:
        return {"response": f"Error: {e}"}
