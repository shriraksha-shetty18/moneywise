import os
import io
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
import pdfplumber

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set. Set it as an environment variable before running.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="MoneyWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """You are MoneyWise, a plain-language financial literacy assistant built for \
first-time earners in India who are confused by financial documents and pushy sales pitches.

You will be given either a document (insurance brochure, credit card terms, loan agreement, \
investment pitch, screenshot/photo of a WhatsApp message from an "advisor") or a plain-language \
description of a financial situation. Respond ONLY in the following markdown structure, filling \
each section with specific, concrete points drawn from the input (never generic filler):

## 🟢 Easy Summary
2-4 short sentences explaining, in plain everyday language, what this product/situation actually is.

## 💰 What It Actually Costs You
Bullet list of fees, premiums, lock-in periods, surrender charges, interest rates, or other costs. \
Be specific with numbers if given. If costs are unclear from the input, say so plainly.

## 🚩 Red Flags
Bullet list of anything unusual, one-sided, high-pressure, or worth being cautious about. If there \
are genuinely no red flags, say "Nothing unusual stood out" and explain briefly why.

## ❓ Questions To Ask Before You Sign or Pay
Bullet list of 3-6 specific, pointed questions the person should ask the advisor/bank/agent.

## ⚠️ Note
One short sentence: this is a financial literacy tool, not personalized investment, legal, or tax \
advice, and the person should verify details directly with the provider or a licensed advisor.

Keep language simple (avoid jargon, or explain it immediately in brackets when unavoidable). Never \
invent numbers that were not in the input. Never recommend a specific competing product to buy."""


def extract_pdf_text(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts).strip()


def stream_gemini_response(parts):
    model = genai.GenerativeModel(model_name=GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(parts, stream=True)

    def generate():
        try:
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:  # surface errors into the stream instead of a silent cutoff
            yield f"\n\n[Error while generating response: {exc}]"

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/api/analyze")
async def analyze(
    text: str = Form(default=""),
    file: UploadFile = File(default=None),
):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Server is missing GEMINI_API_KEY.")

    if not text.strip() and file is None:
        raise HTTPException(status_code=400, detail="Provide text or upload a file.")

    parts = []

    if text.strip():
        parts.append(f"User-provided description:\n{text.strip()}")

    if file is not None:
        content = await file.read()
        content_type = file.content_type or ""

        if content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            extracted = extract_pdf_text(content)
            if not extracted:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from this PDF (it may be a scanned image). "
                           "Try uploading it as an image instead.",
                )
            parts.append(f"Document text extracted from uploaded PDF:\n{extracted}")
        elif content_type.startswith("image/"):
            parts.append({"mime_type": content_type, "data": content})
            parts.append("The above image is a financial document or advisor message. Read and analyze it.")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload a PDF or an image.")

    return stream_gemini_response(parts)


# --- Serve the frontend ---
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
