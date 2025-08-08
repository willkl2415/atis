from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS so GitHub Pages frontend can call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can restrict to your GitHub Pages domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body model
class PromptRequest(BaseModel):
    sector: str
    function: str
    role: str
    prompt: str

@app.post("/generate")
async def generate(req: PromptRequest):
    """
    Handles prompt requests from ATIS Demo.
    Accepts sector, function, role, prompt and sends to GPT-3.5-turbo for fast inference.
    """
    try:
        # Combine inputs into a single prompt string
        full_prompt = (
            f"Sector: {req.sector}\n"
            f"Function: {req.function}\n"
            f"Role: {req.role}\n"
            f"Prompt: {req.prompt}\n\n"
            "Please provide a clear, concise, and context-aware response."
        )

        # Call OpenAI Chat API (fast model)
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=512,
            temperature=0.7
        )

        response_text = completion.choices[0].message.content.strip()

        return {"text": response_text}

    except Exception as e:
        return {"text": f"Error: {str(e)}"}
