# main.py

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create FastAPI app
app = FastAPI()

# Safe path handling for 'static' and 'templates' folders
base_dir = Path(__file__).parent
static_path = base_dir / "static"
templates_path = base_dir / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Set templates folder
templates = Jinja2Templates(directory=templates_path)

# Home route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Response generation route
@app.post("/generate", response_class=HTMLResponse)
async def generate_response(request: Request,
                            sector: str = Form(...),
                            role: str = Form(...),
                            prompt: str = Form(...)):
    try:
        print(f"📥 Received Prompt: {prompt} | Sector: {sector} | Role: {role}")

        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert in {sector} and your role is {role}."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content
        return templates.TemplateResponse("index.html", {
            "request": request,
            "sector": sector,
            "role": role,
            "prompt": prompt,
            "response": answer
        })

    except Exception as e:
        print(f"❌ Error occurred in /generate route:\n{e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "sector": sector,
            "role": role,
            "prompt": prompt,
            "response": "Error generating response."
        })
