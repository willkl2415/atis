import os
import openai
import uvicorn
import asyncio
import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load API key
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# FastAPI app
app = FastAPI()

# CORS policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class GPTRequest(BaseModel):
    sector: str
    role: str
    prompt: str

# Simple in-memory cache
cache = {}

def make_cache_key(sector, role, prompt):
    return hashlib.sha256(f"{sector}|{role}|{prompt}".encode()).hexdigest()

# GPT inference function (OpenAI v1+)
async def get_gpt_response(sector: str, role: str, prompt: str) -> str:
    cache_key = make_cache_key(sector, role, prompt)
    if cache_key in cache:
        return cache[cache_key]

    system_prompt = f"You are an AI assistant supporting someone in the '{role}' role within the '{sector}' sector. Provide clear, practical help in plain English."

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=512
        )
        reply = response.choices[0].message.content.strip()
        cache[cache_key] = reply

        # Limit cache to 10 items
        if len(cache) > 10:
            cache.pop(next(iter(cache)))
        return reply

    except Exception as e:
        return f"Error: {str(e)}"

# Route: POST /generate
@app.post("/generate")
async def generate_response(request: GPTRequest):
    reply = await get_gpt_response(request.sector, request.role, request.prompt)
    return {"response": reply}

# Health check
@app.get("/")
def read_root():
    return {"message": "ATIS External GPT API is running."}

# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
