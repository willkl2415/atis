# main.py — ATIS Optimisation FastAPI backend
# Run: uvicorn main:app --host 0.0.0.0 --port 8002 --workers 1
# Requires: pip install fastapi uvicorn openai python-dotenv

import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# OpenAI Python SDK v1.x
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="ATIS Optimisation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskPayload(BaseModel):
    sector: str
    func: str
    role: str
    prompt: str

def strip_bold_markdown(text: str) -> str:
    return re.sub(r"\*\*", "", text or "")

def build_prompt(sector: str, func: str, role: str, user_prompt: str) -> str:
    # Keep things fast and simple: short context prefix, no over-formatting.
    return (
        f"You are ATIS, a real-time performance support assistant.\n"
        f"User context:\n"
        f"- Sector: {sector}\n"
        f"- Function: {func}\n"
        f"- Role: {role}\n\n"
        f"Instruction:\n"
        f"Answer clearly in plain text. No markdown bold. No lists unless necessary. Be concise and practical.\n\n"
        f"User prompt:\n"
        f"{user_prompt}"
    )

@app.get("/")
async def root():
    return JSONResponse({"ok": True, "service": "ATIS Optimisation API"})

@app.post("/api/ask")
async def api_ask(payload: AskPayload):
    prompt = build_prompt(payload.sector, payload.func, payload.role, payload.prompt)

    # gpt-3.5-turbo for speed; adjust if you need higher quality
    model_name = "gpt-3.5-turbo"

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are ATIS, a fast, helpful assistant. Reply in plain text without markdown bold."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600,
        )
        answer = resp.choices[0].message.content or ""
        answer = strip_bold_markdown(answer).strip()
        return JSONResponse({"answer": answer})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Optional: serve static files if you drop index.html/roles.js/script.js in the same directory.
# Simple dev helper: GET /app to download index.html quickly.
@app.get("/app")
async def get_index():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    return JSONResponse({"error": "index.html not found"}, status_code=404)
