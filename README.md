# MoneyWise — Financial Document Explainer

Paste a financial situation or upload a document (insurance brochure, credit card
terms, loan agreement, investment pitch, or a screenshot of an advisor's WhatsApp
message) and get a plain-language breakdown: what it is, what it costs, red flags,
and questions to ask before signing.

 Building & Deploying an AI Web Application on AWS project.

## Tech stack
- **Frontend:** HTML / CSS / vanilla JavaScript , streamed responses
- **Backend:** Python FastAPI
- **LLM:** Google Gemini API (`gemini-3.5-flash-lite`) 
- **PDF parsing:** pdfplumber (server-side text extraction)
- **Images:** sent directly to Gemini's multimodal input  
- **Containerization:** Docker
- **Deployment target:** AWS Elastic Beanstalk 

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
2. Create an API key  

## 2. Run locally (without Docker)
```bash
cd backend
cp .env.example .env
# edit .env and paste your real GEMINI_API_KEY

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# from the backend/ folder:
Windows (PowerShell): $env:GEMINI_API_KEY="your_key_here"
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

## 4. Deploy to AWS (Elastic Beanstalk, Docker platform)

**Steps (AWS Console, no EB CLI needed):**

1. Zip your project folder (must include `Dockerfile`, `Dockerrun.aws.json`, `backend/`,
   and `frontend/` at the top level of the zip — not nested inside an extra folder).
   Exclude `venv/`, `__pycache__/`, and your real `.env` file. The `Dockerrun.aws.json`
   file tells Elastic Beanstalk to route incoming traffic (port 80) to your container's
   port 8000 — it's already included in this project.
2. Go to the [Elastic Beanstalk console](https://console.aws.amazon.com/elasticbeanstalk)
   → **Create application**.
3. **Application name:** `moneywise`  
4. **Platform:** choose **Docker**  
5. **Application code:** choose **Upload your code**, and upload the zip from step 1.
6. **Environment tier:** Web server environment.
7. **Instance type:** pick a free-tier eligible type (e.g. `t2.micro` or `t3.micro`) in
   the environment's configuration.
8. Under **Configuration → Software**, add environment variables:
   - `GEMINI_API_KEY` = your real key
   - `GEMINI_MODEL` = `gemini-3.5-flash-lite`
    
9. Click **Create environment**. Elastic Beanstalk provisions an EC2 instance, builds
   your Dockerfile into a container, and runs it — this takes a few minutes.
10. Once the environment status is "Healthy", Elastic Beanstalk gives you a public
    URL .

**To redeploy after code changes:** re-zip the project and use **Upload and deploy**
on the environment's dashboard.

## How the AI integration works
- User input (pasted text and/or an uploaded PDF/image) is sent to `POST /api/analyze`.
- PDFs are parsed server-side with `pdfplumber` to extract raw text.
- Images are passed directly to Gemini as multimodal input — Gemini reads the image itself.
- The backend calls Gemini with a fixed system prompt that forces a structured response:
  🟢 Easy Summary, 💰 Costs, 🚩 Red Flags, ❓ Questions to Ask, ⚠️ Disclaimer.
- The response is streamed back to the browser chunk-by-chunk (`StreamingResponse`) and
  rendered progressively in the UI as it arrives 

## Limitations / disclaimer
MoneyWise is a financial **literacy** tool. It does not give personalized investment, legal,
or tax advice, and users should verify details with the actual provider or a licensed advisor.
