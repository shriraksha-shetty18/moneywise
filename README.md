# MoneyWise — Financial Document Explainer

Paste a financial situation or upload a document (insurance brochure, credit card
terms, loan agreement, investment pitch, or a screenshot of an advisor's WhatsApp
message) and get a plain-language breakdown: what it is, what it costs, red flags,
and questions to ask before signing.

Built for the Vibe Coding: Building & Deploying an AI Web Application on AWS project.

## Tech stack
- **Frontend:** HTML / CSS / vanilla JavaScript (no framework), streamed responses
- **Backend:** Python FastAPI
- **LLM:** Google Gemini API (`gemini-2.0-flash`), streamed token-by-token
- **PDF parsing:** pdfplumber (server-side text extraction)
- **Images:** sent directly to Gemini's multimodal input (no separate OCR needed)
- **Containerization:** Docker
- **Deployment target:** AWS App Runner (or Elastic Beanstalk / ECS — any container host works)

## Project structure
```
moneywise/
├── backend/
│   ├── main.py            # FastAPI app, /api/analyze endpoint, Gemini streaming
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── Dockerfile
└── README.md
```

## 1. Get a Gemini API key
1. Go to https://aistudio.google.com/apikey
2. Create an API key (free tier is enough for this project)
3. Copy it — you'll need it below

## 2. Run locally (without Docker)
```bash
cd backend
cp .env.example .env
# edit .env and paste your real GEMINI_API_KEY

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# from the backend/ folder:
export GEMINI_API_KEY=your_key_here   # Windows (PowerShell): $env:GEMINI_API_KEY="your_key_here"
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000 in your browser.

## 3. Run locally with Docker
```bash
cd moneywise
docker build -t moneywise .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here moneywise
```
Open http://localhost:8000.

## 4. Deploy to AWS (App Runner — simplest path)

**Option A: Deploy from a container registry (ECR)**
1. Create an ECR repository:
   ```bash
   aws ecr create-repository --repository-name moneywise
   ```
2. Authenticate Docker to ECR, then build, tag, and push:
   ```bash
   aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<your-region>.amazonaws.com

   docker build -t moneywise .
   docker tag moneywise:latest <account-id>.dkr.ecr.<your-region>.amazonaws.com/moneywise:latest
   docker push <account-id>.dkr.ecr.<your-region>.amazonaws.com/moneywise:latest
   ```
3. In the AWS Console, go to **App Runner → Create service**.
4. Source: **Container registry** → select your ECR image.
5. Under **Environment variables**, add `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) —
   **do not** bake the key into the image or commit it to git.
6. Port: `8000`. CPU/memory: smallest tier is fine for this project (free-tier friendly).
7. Deploy. App Runner gives you a public HTTPS URL — that's your live app URL for submission.

**Option B: Deploy straight from GitHub**
1. Push this project to a GitHub repo (make sure `.env` is in `.gitignore` and never committed).
2. App Runner → Create service → Source: **Source code repository** → connect your repo.
3. App Runner detects the `Dockerfile` automatically (deployment type: **Automatic** or **Manual**, your choice).
4. Add the `GEMINI_API_KEY` environment variable in the App Runner configuration.
5. Deploy and grab the public URL.

### Cost & safety notes
- App Runner's smallest configuration falls within typical AWS free-tier/low-cost usage —
  set a **AWS Budget alert** (Billing → Budgets) regardless, as required by the project guidelines.
- Never put `GEMINI_API_KEY` in frontend code, `Dockerfile`, or version control — only as an
  environment variable on the hosting platform.

## How the AI integration works
- User input (pasted text and/or an uploaded PDF/image) is sent to `POST /api/analyze`.
- PDFs are parsed server-side with `pdfplumber` to extract raw text.
- Images are passed directly to Gemini as multimodal input — Gemini reads the image itself.
- The backend calls Gemini with a fixed system prompt that forces a structured response:
  🟢 Easy Summary, 💰 Costs, 🚩 Red Flags, ❓ Questions to Ask, ⚠️ Disclaimer.
- The response is streamed back to the browser chunk-by-chunk (`StreamingResponse`) and
  rendered progressively in the UI as it arrives, rather than waiting for the full answer.

## Limitations / disclaimer
MoneyWise is a financial **literacy** tool. It does not give personalized investment, legal,
or tax advice, and users should verify details with the actual provider or a licensed advisor.
