# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os, openai

# ---- App ----
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok for public demo; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
def root():
    return {"service": "ATIS API", "status": "ok", "message": "Use POST /generate with { industry, function, role, prompt }."}

@app.post("/generate")
async def generate(req: Request):
    body = await req.json()
    industry = body.get("industry", "").strip()
    function = body.get("function", "").strip()
    role = body.get("role", "").strip()
    prompt = body.get("prompt", "").strip()

    if not (industry and role and prompt):
        return {"text": "Please choose an industry and role, and enter a prompt."}

    # Super-light system message for speed + consistency
    system = (
        "You are ATIS: a rapid performance-support assistant. "
        "Reply in clear, plain text. No markdown formatting, no lists unless the user asks."
    )

    user = (
        f"Context: Industry={industry}; Function={function or 'n/a'}; Role={role}.\n"
        f"Question: {prompt}\n"
        "Answer directly and concisely."
    )

    try:
        # Use the quickest models; pick one you’ve confirmed is fastest in your region/account:
        #   - 'gpt-3.5-turbo-0125' (very fast), or
        #   - 'gpt-4o-mini' (great speed/quality), uncomment whichever you prefer.
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            max_tokens=320,
            temperature=0.2,
            # These help keep latency tight:
            n=1,
        )
        text = response.choices[0].message["content"].strip()
        return {"text": text}
    except Exception as e:
        return {"text": f"Error: {e}"}
