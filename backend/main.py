"""
Signal — Contradiction Catcher
FastAPI backend that reads a project communication thread and detects
conflicting claims between speakers (deadlines, scope, ownership),
then triggers a clarification-flag action instead of a passive summary.
"""

import os
import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Groq exposes an OpenAI-compatible API, so the same SDK works —
# we just point base_url at Groq. Free tier, no credit card required.
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

app = FastAPI(title="Signal API", version="0.1.0")

# Allow the local Vite dev server and any deployed frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your deployed frontend URL before submitting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request / response models ----------

class AnalyzeRequest(BaseModel):
    text: str


class Contradiction(BaseModel):
    topic: str
    speaker_a: str
    claim_a: str
    speaker_b: str
    claim_b: str
    severity: str  # "low" | "medium" | "high"


class AnalyzeResponse(BaseModel):
    has_contradiction: bool
    contradictions: List[Contradiction]
    summary: str
    action: str  # "flag_conflict" | "summarize"
    clarification_message: Optional[str] = None


# ---------- Function (tool) calling schema ----------
# We force the model to return structured data instead of free text,
# so the frontend can render + act on it deterministically.

ANALYSIS_TOOL = {
    "type": "function",
    "function": {
        "name": "report_analysis",
        "description": (
            "Report whether the project communication thread contains any "
            "contradicting claims between two or more speakers on the same "
            "topic (e.g. deadlines, scope, ownership, priorities)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "has_contradiction": {
                    "type": "boolean",
                    "description": "True if two or more speakers made conflicting claims.",
                },
                "contradictions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Short topic label, e.g. 'Launch deadline' or 'Scope: login redesign'.",
                            },
                            "speaker_a": {"type": "string"},
                            "claim_a": {"type": "string"},
                            "speaker_b": {"type": "string"},
                            "claim_b": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "How disruptive this contradiction would be if left unresolved.",
                            },
                        },
                        "required": [
                            "topic",
                            "speaker_a",
                            "claim_a",
                            "speaker_b",
                            "claim_b",
                            "severity",
                        ],
                    },
                },
                "summary": {
                    "type": "string",
                    "description": "One or two sentence plain-language summary of the thread.",
                },
            },
            "required": ["has_contradiction", "contradictions", "summary"],
        },
    },
}

SYSTEM_PROMPT = """You are Signal, an assistant that reads project communication \
threads (chat logs, email threads, meeting notes) and looks specifically for \
CONTRADICTIONS: cases where two different speakers make conflicting claims about \
the same topic — deadlines, scope, ownership, priorities, or decisions.

Rules:
- Only report a contradiction when two claims about the SAME topic genuinely conflict.
- Do not invent speakers or claims that are not in the text.
- If nothing conflicts, return has_contradiction = false and an empty contradictions list.
- Always call the report_analysis function with your findings — never reply in plain text.
"""


def build_clarification_message(c: Contradiction) -> str:
    return (
        f"@{c.speaker_a} and @{c.speaker_b} — I noticed different info on "
        f"\"{c.topic}\": {c.speaker_a} said \"{c.claim_a}\", but {c.speaker_b} said "
        f"\"{c.claim_b}\". Can you confirm which one is correct?"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not set on the server. Add it to backend/.env",
        )

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Thread:\n\n{req.text}"},
            ],
            tools=[ANALYSIS_TOOL],
            tool_choice={"type": "function", "function": {"name": "report_analysis"}},
            temperature=0,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model request failed: {e}")

    tool_calls = completion.choices[0].message.tool_calls
    if not tool_calls:
        raise HTTPException(status_code=502, detail="Model did not return structured analysis")

    try:
        args = json.loads(tool_calls[0].function.arguments)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Could not parse model output")

    contradictions = [Contradiction(**c) for c in args.get("contradictions", [])]
    has_contradiction = bool(args.get("has_contradiction")) and len(contradictions) > 0

    # ---- This is the "trigger" step: decide + act, not just report ----
    if has_contradiction:
        action = "flag_conflict"
        # Use the highest-severity contradiction to build the triggered message.
        top = sorted(
            contradictions,
            key=lambda c: {"high": 0, "medium": 1, "low": 2}.get(c.severity, 1),
        )[0]
        clarification_message = build_clarification_message(top)
    else:
        action = "summarize"
        clarification_message = None

    return AnalyzeResponse(
        has_contradiction=has_contradiction,
        contradictions=contradictions,
        summary=args.get("summary", ""),
        action=action,
        clarification_message=clarification_message,
    )


@app.get("/samples")
def samples():
    """Sample threads for the demo — used by the frontend's 'Try an example' buttons."""
    return {
        "deadline_conflict": (
            "Priya (9:02 AM): Ok team, let's plan to ship the onboarding flow by Friday.\n"
            "Raj (9:15 AM): Sounds good, I'll have the API ready before then.\n"
            "Meera (11:40 AM): Just confirming — Monday works for everyone on the ship date?\n"
            "Raj (11:42 AM): Yep, Monday's fine for me.\n"
        ),
        "scope_conflict": (
            "Arjun (2:10 PM): Heads up, we're cutting the login redesign from this sprint, focusing on checkout only.\n"
            "Sana (2:30 PM): Got it, makes sense given the timeline.\n"
            "Karan (4:05 PM): For the login redesign, should the new password reset flow use email or SMS OTP?\n"
        ),
        "no_conflict": (
            "Dev (10:00 AM): Standup notes — checkout API is done, QA starts tomorrow.\n"
            "Ishaan (10:02 AM): Nice, I'll prep the test cases today.\n"
            "Dev (10:03 AM): Sounds good, let's sync at 4pm if anything blocks.\n"
        ),
    }
