import os
import openai
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
import hashlib

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Init FastAPI
app = FastAPI()

# CORS policy for local/frontend access
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

# In-memory LRU cache (size: 10)
cache = {}

def make_cache_key(sector, role, prompt):
    return hashlib.sha256(f"{sector}|{role}|{prompt}".encode()).hexdigest()

# GPT Inference Function
async def get_gpt_response(sector: str, role: str, prompt: str) -> str:
    cache_key = make_cache_key(sector, role, prompt)
    if cache_key in cache:
        return cache[cache_key]

    # Compress prompt for speed
    system_msg = f"You are an AI assistant supporting someone in the '{role}' role within the '{sector}' sector. Provide clear, practical help in plain English."
    user_msg = prompt.strip()

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=512,
            response_format="text"
        )
        reply = response.choices[0].message.content.strip()
        cache[cache_key] = reply

        # Trim cache to last 10 entries
        if len(cache) > 10:
            cache.pop(next(iter(cache)))
        return reply

    except Exception as e:
        return f"Error: {str(e)}"

# POST Endpoint
@app.post("/generate")
async def generate_gpt_response(request: GPTRequest):
    response = await get_gpt_response(request.sector, request.role, request.prompt)
    return {"response": response}

# Health Check
@app.get("/")
def read_root():
    return {"message": "ATIS External GPT API is running."}

# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
