# Signal — Backend

FastAPI service that analyzes a project communication thread and detects
contradictions between speakers, then triggers a clarification action.

Uses **Groq** (free tier, no credit card) via its OpenAI-compatible API.

## Get a free API key

1. Go to https://console.groq.com and sign up with email or Google.
2. Go to **API Keys** → **Create API Key** → copy it (starts with `gsk_`).
3. No billing setup, no credit card needed.

Free tier limits: 30 requests/min, 14,400 requests/day — plenty for this project.

## Run locally

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your real Groq key into .env
uvicorn main:app --reload --port 8000
```

API will be live at http://localhost:8000
Interactive docs: http://localhost:8000/docs

## Endpoints

- `GET /health` — liveness check
- `GET /samples` — sample demo threads (deadline conflict, scope conflict, no conflict)
- `POST /analyze` — body: `{ "text": "..." }` → returns contradictions + triggered action

## Swapping models

Set `GROQ_MODEL` in `.env`. Good options that support tool calling:
- `llama-3.3-70b-versatile` (default — most accurate for this task)
- `llama-3.1-8b-instant` (faster, less reliable on subtle contradictions)

## Deploy (Render, free tier)

1. Push this repo to GitHub.
2. On Render: New → Web Service → connect repo, root directory `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable `GROQ_API_KEY` in Render's dashboard.
6. Copy the deployed URL into the frontend's `VITE_API_URL`.
