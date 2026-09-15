
## Quick start (local demo)

```bash
# Terminal 1 — backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your free GROQ_API_KEY
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, click one of the three example threads
(deadline conflict / scope conflict / no conflict), and hit **Scan thread**.

## Demo script

1. Open the app, paste the **deadline conflict** example.
2. Hit Scan — narrate what's happening while it runs.
3. Point out the contradiction card (Friday vs. Monday) and the triggered
   clarification message underneath — this is the differentiator: it doesn't
   just summarize, it acts.
4. Paste the **no conflict** example to show it doesn't false-flag.
5. Close with the one-line pitch above.
