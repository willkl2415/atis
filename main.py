from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
import os

# ---------- API KEY ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

openai.api_key = OPENAI_API_KEY

# ---------- FastAPI APP ----------
app = FastAPI()

# Allow all CORS (GitHub Pages frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request Schema ----------
class PromptRequest(BaseModel):
    sector: str
    func: str
    role: str
    prompt: str

# ---------- Root ----------
@app.get("/")
async def root():
    return {"message": "ATIS API streaming endpoint is live"}

# ---------- Streaming Endpoint ----------
@app.post("/generate")
async def generate_stream(request: PromptRequest):
    """
    Streams GPT-3.5-Turbo output token-by-token for ChatGPT-like instant responses.
    """

    # Build the role-specific context
    context = (
        f"You are ATIS (AI-powered Training Intelligence System). "
        f"Provide a clear, concise, role-specific answer in plain text with no markdown bold.\n\n"
        f"Sector: {request.sector}\n"
        f"Function: {request.func}\n"
        f"Role: {request.role}\n\n"
        f"User question: {request.prompt}"
    )

    # Define a generator that yields streamed tokens
    def stream_tokens():
        try:
            stream = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": context}],
                max_tokens=500,
                temperature=0.7,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.get("content", "")
                if delta:
                    yield delta
        except Exception as e:
            yield f"[Error: {str(e)}]"

    # Return the streaming response
    return StreamingResponse(stream_tokens(), media_type="text/plain; charset=utf-8")
