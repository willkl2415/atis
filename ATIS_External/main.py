from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

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
        print(f"📥 Received Prompt: {prompt} | Sector: {sector} | Role: {role}")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
        print(f"❌ Error occurred in /generate route:\n\n{e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "sector": sector,
            "role": role,
            "prompt": prompt,
            "response": "Error generating response."
        })
