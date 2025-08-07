# main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# -------- Config --------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Frontend origins allowed to call this API (add more if needed)
ALLOWED_ORIGINS = [
    "https://willkl2415.github.io",   # GitHub Pages root
    "https://willkl2415.github.io/atis",  # your demo path
    "http://localhost:8002",          # local testing
    "http://127.0.0.1:8002"
]

app = FastAPI(title="ATIS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    sector: str
    function: str | None = None
    role: str
    prompt: str

class GenerateResponse(BaseModel):
    response: str

@app.get("/")
def root():
    return {
        "service": "ATIS API",
        "status": "ok",
        "message": "Use POST /generate with { sector, function, role, prompt }."
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        # System prompt keeps output clean (no markdown bold)
        system_msg = (
            "You are ATIS, an AI performance support assistant. "
            "Always answer in clear plain text with short paragraphs and numbered steps when useful. "
            "Do not use markdown formatting like **bold** or bullet symbols unless asked."
        )

        user_context = (
            f"Sector: {req.sector}\n"
            f"Function: {req.function or 'N/A'}\n"
            f"Role: {req.role}\n\n"
            f"User question: {req.prompt}"
        )

        # Light, fast model for demo (change to gpt-4o-mini / gpt-4.1 if you want)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_context}
            ],
            temperature=0.4,
            max_tokens=700
        )

        text = completion.choices[0].message.content.strip()
        return GenerateResponse(response=text)
    except Exception as e:
        # Log to server console and return clean client error
        print("ATIS API error:", e)
        raise HTTPException(status_code=500, detail="Generation failed.")
