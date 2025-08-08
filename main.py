import os
import time
import asyncio
from typing import Dict, Any, Tuple

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="ATIS API", version="1.0.0")

# Allow your GitHub Pages site + localhost during dev
ALLOWED_ORIGINS = [
    "https://willkl2415.github.io",   # GitHub Pages root
    "https://willkl2415.github.io/atis",
    "http://127.0.0.1:8002",
    "http://localhost:8002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# OpenAI client
# -----------------------------
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

# We'll set a per-request timeout later via with_options
client = OpenAI()

# -----------------------------
# Simple in-memory cache (TTL)
# -----------------------------
CACHE: Dict[str, Tuple[float, str]] = {}  # key -> (expires_at_epoch, text)
CACHE_TTL_SECONDS = 600                   # 10 minutes
CACHE_MAX_KEYS = 64

def _cache_get(key: str) -> str | None:
    item = CACHE.get(key)
    if not item:
        return None
    exp, val = item
    if time.time() > exp:
        CACHE.pop(key, None)
        return None
    return val

def _cache_put(key: str, value: str) -> None:
    # Basic size control
    if len(CACHE) >= CACHE_MAX_KEYS:
        # remove oldest (not perfect LRU, but fine for our needs)
        oldest_key = next(iter(CACHE))
        CACHE.pop(oldest_key, None)
    CACHE[key] = (time.time() + CACHE_TTL_SECONDS, value)

# -----------------------------
# Schemas
# -----------------------------
class GenerateIn(BaseModel):
    sector: str
    func: str
    role: str
    prompt: str

class GenerateOut(BaseModel):
    text: str

# -----------------------------
# Health + root
# -----------------------------
@app.get("/")
def root():
    return {"service": "ATIS API", "status": "ok", "message": "Use POST /generate with { sector, function, role, prompt }."}

@app.get("/health")
def health():
    return {"ok": True, "ts": int(time.time())}

# -----------------------------
# Generate endpoint (fast path)
# -----------------------------
SYSTEM_PROMPT = (
    "You are ATIS, a realtime coaching co‑pilot. "
    "Give concise, actionable guidance tailored to the user's sector, function, and role. "
    "Avoid markdown bold/italics; output plain, readable text with short bullets if useful."
)

MODEL = "gpt-4o-mini"       # very fast + cheap; good quality
MAX_OUTPUT_TOKENS = 180     # keep answers snappy
TEMPERATURE = 0.4

@app.post("/generate", response_model=GenerateOut)
async def generate(body: GenerateIn):
    # --- cache key
    key = f"{body.sector}||{body.func}||{body.role}||{body.prompt.strip()}"
    cached = _cache_get(key)
    if cached is not None:
        return {"text": cached}

    # --- construct compact user prompt
    user_content = (
        f"Sector: {body.sector}\n"
        f"Function: {body.func}\n"
        f"Role: {body.role}\n\n"
        f"Question: {body.prompt.strip()}\n\n"
        "Constraints: plain text only (no **bold**). Keep it crisp."
    )

    # --- make the OpenAI request with a hard 6s timeout
    oai = client.with_options(timeout=6.0)  # seconds

    async def _call_openai() -> str:
        # Using the Responses API (new SDK) for speed and simplicity
        resp = oai.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            # force plain text
            response_format={"type": "text"},
        )
        # responses.create returns text in a friendly place:
        text = resp.output_text or ""
        return text.strip() or "No response."

    try:
        text: str = await asyncio.wait_for(_call_openai(), timeout=6.5)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Upstream timeout after 6s. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # --- save to cache and return
    _cache_put(key, text)
    return {"text": text}
