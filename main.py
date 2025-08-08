import os, time, hashlib, json
from collections import OrderedDict
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

# Fast models first for sub‑second replies
PRIMARY_MODEL   = os.getenv("ATIS_MODEL_PRIMARY", "gpt-4o-mini")
FALLBACK_MODEL  = os.getenv("ATIS_MODEL_FALLBACK", "gpt-3.5-turbo")
MAX_TOKENS      = int(os.getenv("ATIS_MAX_TOKENS", "256"))
TEMPERATURE     = float(os.getenv("ATIS_TEMPERATURE", "0.6"))

# Hard timeouts so calls never hang forever
# (SDK v1 allows per-call timeout; we enforce a short read timeout)
REQUEST_TIMEOUT_SECONDS = float(os.getenv("ATIS_TIMEOUT", "6.0"))

# CORS: allow your GitHub Pages site
GHPAGES = "https://willkl2415.github.io"

# ----------------------------
# Client (reused for pooling)
# ----------------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Tiny TTL LRU Cache
# ----------------------------
class TTL_LRU:
    def __init__(self, capacity: int = 20, ttl_seconds: int = 600):
        self.capacity = capacity
        self.ttl = ttl_seconds
        self.data: OrderedDict[str, Any] = OrderedDict()

    def _now(self) -> float:
        return time.time()

    def get(self, k: str):
        item = self.data.get(k)
        if not item:
            return None
        value, ts = item
        if self._now() - ts > self.ttl:
            # expired
            try: del self.data[k]
            except KeyError: pass
            return None
        self.data.move_to_end(k)
        return value

    def set(self, k: str, v: Any):
        self.data[k] = (v, self._now())
        self.data.move_to_end(k)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)

cache = TTL_LRU(capacity=20, ttl_seconds=600)

def cache_key(payload: Dict[str, Any]) -> str:
    # normalize and hash
    key_src = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(key_src.encode("utf-8")).hexdigest()

# ----------------------------
# FastAPI
# ----------------------------
app = FastAPI(title="ATIS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[GHPAGES, "http://127.0.0.1:8002", "http://localhost:8002", "*"],  # relax if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenIn(BaseModel):
    sector: str
    func: str
    role: str
    prompt: str

def system_prompt(sector: str, func: str, role: str) -> str:
    # Keep it short for speed; no heavy instructions.
    return (
        "You are ATIS, a real‑time coaching assistant. "
        "Answer clearly and directly for the user's sector, function, and role. "
        "Avoid markdown bold. Keep it concise and actionable.\n"
        f"Sector: {sector}\nFunction: {func}\nRole: {role}\n"
    )

def call_model(messages, model_name: str):
    # Per‑request read timeout via kwargs
    # SDK v1 supports 'timeout' kw on .create
    return client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

@app.get("/")
def root():
    return {"service": "ATIS API", "status": "ok", "message": "Use POST /generate with { sector, function, role, prompt }."}

@app.get("/ping")
def ping():
    return {"pong": True, "ts": time.time()}

@app.post("/generate")
def generate(body: GenIn, request: Request):
    t0 = time.time()

    # Build cache key
    payload = {
        "sector": body.sector.strip(),
        "func": body.func.strip(),
        "role": body.role.strip(),
        "prompt": body.prompt.strip(),
        "model": PRIMARY_MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }
    key = cache_key(payload)
    cached = cache.get(key)
    if cached:
        return {
            "text": cached,
            "model": PRIMARY_MODEL,
            "cached": True,
            "elapsed_ms": int((time.time() - t0) * 1000),
        }

    sys_msg = {"role": "system", "content": system_prompt(body.sector, body.func, body.role)}
    user_msg = {"role": "user", "content": body.prompt.strip()}
    msgs = [sys_msg, user_msg]

    # Try fast primary model, then fallback
    text = None
    used_model = PRIMARY_MODEL
    try:
        resp = call_model(msgs, PRIMARY_MODEL)
        text = (resp.choices[0].message.content or "").strip()
        used_model = PRIMARY_MODEL
    except Exception:
        # Fallback once (keeps ATIS responsive)
        try:
            resp = call_model(msgs, FALLBACK_MODEL)
            text = (resp.choices[0].message.content or "").strip()
            used_model = FALLBACK_MODEL
        except Exception as e2:
            elapsed = int((time.time() - t0) * 1000)
            return {
                "text": f"Upstream model timed out. Please try again.\n({type(e2).__name__})",
                "model": None,
                "cached": False,
                "elapsed_ms": elapsed,
            }

    # Sanitize minor markdown (no bold)
    if text:
        text = text.replace("**", "")

    cache.set(key, text)
    elapsed = int((time.time() - t0) * 1000)
    return {"text": text, "model": used_model, "cached": False, "elapsed_ms": elapsed}
