import os, time, json, hashlib
from collections import OrderedDict
from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# ---------- Config ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

PRIMARY_MODEL  = os.getenv("ATIS_MODEL_PRIMARY", "gpt-4o-mini")
FALLBACK_MODEL = os.getenv("ATIS_MODEL_FALLBACK", "gpt-3.5-turbo")
MAX_TOKENS     = int(os.getenv("ATIS_MAX_TOKENS", "200"))
TEMPERATURE    = float(os.getenv("ATIS_TEMPERATURE", "0.6"))
REQ_TIMEOUT    = float(os.getenv("ATIS_TIMEOUT", "6.0"))  # hard per-call timeout

GHPAGES = "https://willkl2415.github.io"

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Tiny TTL LRU cache ----------
class TTL_LRU:
    def __init__(self, cap=20, ttl=600):
        self.cap, self.ttl = cap, ttl
        self.data: OrderedDict[str, Any] = OrderedDict()
    def _now(self): return time.time()
    def get(self, k:str):
        v = self.data.get(k)
        if not v: return None
        val, ts = v
        if self._now() - ts > self.ttl:
            self.data.pop(k, None); return None
        self.data.move_to_end(k); return val
    def set(self, k:str, val:Any):
        self.data[k] = (val, self._now()); self.data.move_to_end(k)
        if len(self.data) > self.cap: self.data.popitem(last=False)

cache = TTL_LRU()

def cache_key(obj: Dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

# ---------- FastAPI ----------
app = FastAPI(title="ATIS API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[GHPAGES, "http://127.0.0.1:8002", "http://localhost:8002", "*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class GenIn(BaseModel):
    sector: str
    func: str
    role: str
    prompt: str

def system_prompt(sector, func, role) -> str:
    return (
        "You are ATIS, a real‑time coaching assistant. "
        "Answer clearly and directly for the user's sector, function, and role. "
        "Avoid markdown bold. Keep it concise and actionable.\n"
        f"Sector: {sector}\nFunction: {func}\nRole: {role}\n"
    )

@app.get("/")
def root():
    return {"service":"ATIS API","status":"ok","message":"Use POST /generate or /generate_stream."}

@app.get("/ping")
def ping():
    return {"pong": True, "ts": time.time()}

# ---------- Non‑streaming (kept for compatibility) ----------
@app.post("/generate")
def generate(body: GenIn):
    t0 = time.time()
    payload = {
        "sector": body.sector.strip(),
        "func": body.func.strip(),
        "role": body.role.strip(),
        "prompt": body.prompt.strip(),
        "model": PRIMARY_MODEL, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
    }
    key = cache_key(payload)
    c = cache.get(key)
    if c:
        return {"text": c, "model": PRIMARY_MODEL, "cached": True, "elapsed_ms": int((time.time()-t0)*1000)}

    msgs = [
        {"role":"system","content": system_prompt(body.sector, body.func, body.role)},
        {"role":"user","content": body.prompt.strip()},
    ]

    def call(model):
        return client.chat.completions.create(
            model=model, messages=msgs, temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS, timeout=REQ_TIMEOUT,
        )

    text, used = None, PRIMARY_MODEL
    try:
        r = call(PRIMARY_MODEL)
        text = (r.choices[0].message.content or "").strip()
    except Exception:
        try:
            r = call(FALLBACK_MODEL)
            text = (r.choices[0].message.content or "").strip()
            used = FALLBACK_MODEL
        except Exception as e2:
            return {"text": f"Upstream model timed out. Try again.", "model": None, "cached": False,
                    "elapsed_ms": int((time.time()-t0)*1000)}

    text = text.replace("**","") if text else "No content."
    cache.set(key, text)
    return {"text": text, "model": used, "cached": False, "elapsed_ms": int((time.time()-t0)*1000)}

# ---------- Streaming (SSE-like over plain chunked) ----------
@app.post("/generate_stream")
def generate_stream(body: GenIn):
    msgs = [
        {"role":"system","content": system_prompt(body.sector, body.func, body.role)},
        {"role":"user","content": body.prompt.strip()},
    ]
    def token_gen():
        try:
            stream = client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=msgs,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=True,
                timeout=REQ_TIMEOUT,
            )
        except Exception:
            stream = client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=msgs,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=True,
                timeout=REQ_TIMEOUT,
            )
        yield ""  # flush headers quickly
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta
        # done
    return StreamingResponse(token_gen(), media_type="text/plain; charset=utf-8")
