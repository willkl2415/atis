# main.py  — ATIS Demo backend (FastAPI + OpenAI)
# Works on Render. Expects OPENAI_API_KEY in the environment.

import os
from typing import Optional, Dict, Tuple
from collections import OrderedDict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception as e:  # pragma: no cover
    OpenAI = None  # type: ignore

# -----------------------------
# Config (env overrides allowed)
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("ATIS_MODEL", "gpt-3.5-turbo")
TEMPERATURE = float(os.getenv("ATIS_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("ATIS_MAX_TOKENS", "512"))

# -----------------------------
# App
# -----------------------------
app = FastAPI(title="ATIS API", version="1.0.0")

# Allow the GitHub Pages frontend to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For demo; restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# OpenAI client (lazy init)
# -----------------------------
_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

# -----------------------------
# Simple in‑memory LRU cache
# -----------------------------
class LRU:
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.store: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> Optional[str]:
        if key in self.store:
            self.store.move_to_end(key)
            return self.store[key]
        return None

    def set(self, key: str, value: str):
        self.store[key] = value
        self.store.move_to_end(key)
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)

cache = LRU(capacity=10)

# -----------------------------
# Request/Response models
# -----------------------------
class GenRequest(BaseModel):
    sector: str = Field("", description="Selected sector")
    func: str = Field("", description="Selected function")
    role: str = Field("", description="Selected role")
    prompt: str = Field("", description="User's question")

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def root():
    return {
        "service": "ATIS API",
        "status": "ok",
        "message": "Use POST /generate with { sector, function, role, prompt }."
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}

# -----------------------------
# Core generate endpoint
# -----------------------------
@app.post("/generate")
def generate(req: GenRequest):
    """
    Returns { "text": "<model output>" }
    (The frontend relies on the 'text' key.)
    """
    # Basic validation
    if not (req.sector and req.func and req.role and req.prompt.strip()):
        # Still return 'text' so the UI displays it
        return {"text": "Please select sector, function, role, and enter a prompt."}

    # Compose a compact, role-aware instruction to keep answers crisp and fast
    system_msg = (
        "You are ATIS, a real-time coaching assistant. "
        "Give clear, practical, sector- and role-specific guidance. "
        "Keep it concise and scannable (bullets welcome). "
        "No markdown formatting like **bold**. No apologies. No disclaimers."
    )
    user_msg = (
        f"Sector: {req.sector}\n"
        f"Function: {req.func}\n"
        f"Role: {req.role}\n"
        f"Prompt: {req.prompt.strip()}\n"
        "Respond with concrete, actionable steps the user can apply immediately."
    )

    # Cache key to speed up repeated demos
    cache_key = f"{MODEL}|{TEMPERATURE}|{MAX_TOKENS}|{user_msg}"
    cached = cache.get(cache_key)
    if cached:
        return {"text": cached}

    # Guard: key missing -> friendly error for demos
    if not OPENAI_API_KEY:
        return {"text": "The service is not configured with an OpenAI API key."}

    try:
        client = get_client()
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        output = (completion.choices[0].message.content or "").strip()
        if not output:
            output = "No content returned from the model."
        cache.set(cache_key, output)
        return {"text": output}

    except Exception as e:
        # Always return a 'text' field so the UI shows something useful
        return {"text": f"Error generating response: {str(e)}"}
