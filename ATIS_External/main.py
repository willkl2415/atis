from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os, uvicorn, hashlib, logging

# Load .env
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atis")

# App init
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve frontend
@app.get("/")
async def serve_ui():
    return FileResponse("test.html")

# Request schema
class GPTRequest(BaseModel):
    sector: str
    role: str
    prompt: str

# Cache
cache = {}

def make_cache_key(sector, role, prompt):
    return hashlib.sha256(f"{sector}|{role}|{prompt}".encode()).hexdigest()

# GPT handler
@app.post("/generate")
async def generate_response(request: GPTRequest):
    logger.info(f"Request: {request.sector} / {request.role} / {request.prompt}")
    cache_key = make_cache_key(request.sector, request.role, request.prompt)
    if cache_key in cache:
        return JSONResponse(content={"response": cache[cache_key]})

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are an AI assistant supporting a {request.role} in {request.sector}"},
                {"role": "user", "content": request.prompt.strip()}
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=512,
            timeout=10
        )
        result = response.choices[0].message.content.strip()
        cache[cache_key] = result
        if len(cache) > 10:
            cache.pop(next(iter(cache)))
        return JSONResponse(content={"response": result})
    except Exception as e:
        logger.error(f"OpenAI Error: {e}")
        return JSONResponse(content={"response": f"Error: {str(e)}"})

# Launch
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
