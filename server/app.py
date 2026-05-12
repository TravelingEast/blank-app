"""
GlassCam AI — companion server

Receives JPEG frames from the Glass app, sends them to Claude vision,
stores results in SQLite, and serves them to the Streamlit dashboard.

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    uvicorn app:app --host 0.0.0.0 --port 5000
"""

import base64
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# ── Constants ──────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "glasscam.db"

# Keep responses short — the only output channel is bone conduction audio
SYSTEM_PROMPT = (
    "You are an AI assistant embedded in a pair of Google Glass worn by the user. "
    "Your responses are spoken aloud through bone conduction — the user cannot see a screen. "
    "Keep every reply to ONE sentence (25 words max). "
    "Be direct and specific. Describe only what is relevant to the user's prompt. "
    "Speak in second person (e.g. 'You are looking at…'). "
    "Skip pleasantries, affirmations, and filler words."
)

# ── Database ───────────────────────────────────────────────────────────────

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS captures (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          TEXT    NOT NULL,
                device_id   TEXT    NOT NULL DEFAULT 'unknown',
                frame_b64   TEXT,
                prompt      TEXT    NOT NULL,
                response    TEXT    NOT NULL,
                model       TEXT    NOT NULL,
                latency_ms  INTEGER
            )
        """)
        conn.commit()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_capture(device_id: str, frame_b64: str, prompt: str,
                 response: str, model: str, latency_ms: int):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO captures (ts, device_id, frame_b64, prompt, response, model, latency_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), device_id, frame_b64,
             prompt, response, model, latency_ms)
        )
        conn.commit()


# ── FastAPI app ────────────────────────────────────────────────────────────

app = FastAPI(title="GlassCam AI Server", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

_anthropic = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.post("/upload_frame")
async def upload_frame(
    frame: UploadFile = File(...),
    prompt: str = Form("Briefly describe what you see in one sentence."),
    model: str = Form("claude-haiku-4-5-20251001"),   # fast model for real-time Glass use
    device_id: str = Form("unknown"),
):
    """
    Accepts a JPEG from Glass, sends it to Claude vision, returns AI text.

    The Glass app also sends X-Device-Id as a header; we prefer the form
    field but fall back gracefully.
    """
    jpeg_bytes = await frame.read()
    if not jpeg_bytes:
        raise HTTPException(status_code=400, detail="Empty frame")

    b64 = base64.standard_b64encode(jpeg_bytes).decode()

    t0 = time.monotonic()
    try:
        message = _anthropic.messages.create(
            model=model,
            max_tokens=100,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}")

    latency_ms = int((time.monotonic() - t0) * 1000)
    response_text = message.content[0].text.strip()

    save_capture(device_id, b64, prompt, response_text, model, latency_ms)

    return {"response": response_text, "latency_ms": latency_ms}


@app.get("/history")
def history(limit: int = 50, device_id: Optional[str] = None):
    """Returns recent captures for the Streamlit dashboard."""
    with get_db() as conn:
        if device_id:
            rows = conn.execute(
                "SELECT id, ts, device_id, prompt, response, model, latency_ms "
                "FROM captures WHERE device_id=? ORDER BY id DESC LIMIT ?",
                (device_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, ts, device_id, prompt, response, model, latency_ms "
                "FROM captures ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


@app.get("/latest_frame")
def latest_frame(device_id: Optional[str] = None):
    """Returns the most recent stored JPEG as image/jpeg for the dashboard."""
    with get_db() as conn:
        if device_id:
            row = conn.execute(
                "SELECT frame_b64 FROM captures WHERE device_id=? AND frame_b64 IS NOT NULL "
                "ORDER BY id DESC LIMIT 1",
                (device_id,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT frame_b64 FROM captures WHERE frame_b64 IS NOT NULL "
                "ORDER BY id DESC LIMIT 1"
            ).fetchone()

    if not row or not row["frame_b64"]:
        raise HTTPException(status_code=404, detail="No frames yet")

    jpeg = base64.b64decode(row["frame_b64"])
    return Response(content=jpeg, media_type="image/jpeg")


@app.delete("/history")
def clear_history():
    """Wipe all stored captures (dashboard button)."""
    with get_db() as conn:
        conn.execute("DELETE FROM captures")
        conn.commit()
    return {"deleted": True}
