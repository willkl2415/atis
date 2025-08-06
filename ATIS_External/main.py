import os
import uvicorn
import asyncio
import hashlib
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment and key
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atis")

# FastAPI app
app = FastAPI()

# Allow frontend access
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

# In-memory cache
cache = {}

def make_cache_key(sector, role, prompt):
    return hashlib.sha256(f"{sector}|{role}|{prompt}".encode()).hexdigest()

# GPT request function
async def get_gpt_response(sector: str, role: str, prompt: str) -> str:
    cache_key = make_cache_key(sector, role, prompt)

    if cache_key in cache:
        logger.info("Cache hit")
        return cache[cache_key]

    system_prompt = f"You are an AI assistant supporting someone in the '{role}' role within the '{sector}' sector. Provide clear, practical help in plain English."

    try:
        logger.info("Sending prompt to OpenAI")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=512,
            timeout=10
        )
        reply = response.choices[0].message.content.strip()
        logger.info("OpenAI response received")

        cache[cache_key] = reply
        if len(cache) > 10:
            cache.pop(next(iter(cache)))
        return reply

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f"Error: {str(e)}"

# POST route
@app.post("/generate")
async def generate_response(request: GPTRequest):
    logger.info(f"Received request: Sector={request.sector}, Role={request.role}, Prompt={request.prompt}")
    reply = await get_gpt_response(request.sector, request.role, request.prompt)
    logger.info(f"Sending response: {reply[:100]}...")
    return {"response": reply}

# GET route
@app.get("/")
def read_root():
    return {"message": "ATIS External GPT API is running."}

# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
