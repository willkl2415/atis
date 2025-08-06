import os
import uvicorn
import asyncio
import hashlib
import logging
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atis")

# App init
app = FastAPI()

# CORS for API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache
cache = {}

# Request schema
class GPTRequest(BaseModel):
    sector: str
    role: str
    prompt: str

# Cache key
def make_cache_key(sector, role, prompt):
    return hashlib.sha256(f"{sector}|{role}|{prompt}".encode()).hexdigest()

# Serve the test.html from local folder
@app.get("/")
async def serve_ui():
    return FileResponse("test.html")

# Handle GPT
@app.post("/generate")
async def generate_response(request: GPTRequest):
    logger.info(f"Request: Sector={request.sector}, Role={request.role}, Prompt={request.prompt}")

    cache_key = make_cache_key(request.sector, request.role, request.prompt)
    if cache_key in cache:
        logger.info("Cache hit")
        return JSONResponse(content={"response": cache[cache_key]})

    system_prompt = f"You are an AI assistant supporting someone in the '{request.role}' role within the '{request.sector}' sector. Provide clear, practical help in plain English."

    try:
        logger.info("Sending to OpenAI...")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt.strip()}
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

        return JSONResponse(content={"response": reply})

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return JSONResponse(content={"response": f"Error: {str(e)}"})

# Start server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
