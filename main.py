import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = os.getenv("ATIS_MODEL", "gpt-4o-mini")  # fast default; fallback inside handler

app = FastAPI(title="ATIS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock down to your domain later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateIn(BaseModel):
    sector: str
    func: str
    role: str
    prompt: str

@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}

@app.post("/generate")
async def generate(body: GenerateIn):
    """
    Fast, no-frills completion.
    Keep tokens modest for snappy responses.
    """
    full_prompt = (
        f"You are an expert in {body.sector}, working in the {body.func} function, "
        f"as a {body.role}. Respond briefly, clearly, and practically.\n\n"
        f"User question: {body.prompt}"
    )

    try:
        # Try the fast model first; if not available on the account, fall back.
        try_models = [MODEL, "gpt-3.5-turbo"]

        last_err = None
        for m in try_models:
            try:
                resp = client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role": "system", "content": "You are ATIS: concise, practical, and context-aware."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=400,     # modest cap for speed
                    temperature=0.6,    # balanced
                )
                text = (resp.choices[0].message.content or "").strip()
                return {"text": text, "model": m}
            except Exception as e:
                last_err = e
                continue

        # if all models failed:
        raise last_err if last_err else RuntimeError("No completion returned.")
    except Exception as e:
        return {"text": f"Error: {str(e)}"}
