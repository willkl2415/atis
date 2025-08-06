# main.py

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate", response_class=HTMLResponse)
async def generate_response(
    request: Request,
    sector: str = Form(...),
    role: str = Form(...),
    prompt: str = Form(...)
):
    try:
        print(f"\U0001F4E5 Received Prompt: {prompt} | Sector: {sector} | Role: {role}")

        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert in {sector}, acting as a {role}."},
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
