# Signal — Contradiction Catcher

**AS-02 · Communication** — ArchScale Guild Hackathon

Most AI communication tools (Slack AI, Notion AI, meeting-note bots) summarize
threads or extract action items. Signal does something narrower and less
covered: it reads a project communication thread and flags when **two people
are unknowingly saying conflicting things** — different deadlines, different
scope calls, different ownership assumptions — and automatically triggers a
clarification request instead of leaving the conflict buried.

## How it works

1. Paste a thread (chat log, email thread, meeting notes) into the UI.
2. The backend sends it to an LLM with a structured function-calling schema
   that forces it to extract claims by topic and compare them across speakers.
   Runs on Groq's free tier — no credit card, no per-token cost.
3. If two claims on the same topic conflict, Signal **triggers** a
   clarification message tagging both people — this is the "act", not just
   "report", step.
4. If nothing conflicts, it falls back to a short plain-language summary.

## Stack

- **Backend:** FastAPI + Groq API, free tier (function calling / tool use)
- **Frontend:** React (Vite), no UI framework — plain CSS with a small design
  token system

## Project structure

```
signal/
├── backend/     FastAPI service — see backend/README.md
└── frontend/    React app — see frontend/README.md
```

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

## Demo script (for the video walkthrough)

1. Open the app, paste the **deadline conflict** example.
2. Hit Scan — narrate what's happening while it runs.
3. Point out the contradiction card (Friday vs. Monday) and the triggered
   clarification message underneath — this is the differentiator: it doesn't
   just summarize, it acts.
4. Paste the **no conflict** example to show it doesn't false-flag.
5. Close with the one-line pitch: *"Other tools tell you what was said.
   Signal tells you what doesn't add up."*
