from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import psycopg2.extras
import os

from db.database import get_connection, init_db
from db.ollama_service import explain_question, chat_about_question
from data.questions_loader import (
    load_questions,
    get_question_by_id,
    get_all_topics,
    get_total_count,
)

app = FastAPI(title="Führerschein AI Trainer")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    init_db()
    print(f"✅ App started — {get_total_count()} questions loaded")


# ─── Pages ───────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/practice", response_class=HTMLResponse)
async def practice_page(request: Request):
    return templates.TemplateResponse("practice.html", {"request": request})


@app.get("/topics", response_class=HTMLResponse)
async def topics_page(request: Request):
    return templates.TemplateResponse("topics.html", {"request": request})


# ─── Questions API ───────────────────────────────────────


@app.get("/api/questions")
async def get_questions(
    topic: Optional[str] = None, status: Optional[str] = None, limit: int = 2500
):
    questions = load_questions()
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM progress")
    progress_rows = {row["question_id"]: row for row in cur.fetchall()}
    cur.close()
    conn.close()

    result = []
    for q in questions:
        prog = progress_rows.get(q["id"], {})
        q_with_status = {
            **q,
            "status": prog.get("status", "unseen"),
            "attempts": prog.get("attempts", 0),
            "autovio": bool(prog.get("autovio", False)),
            "starred": bool(prog.get("starred", False)),
        }
        if (
            topic
            and topic.lower() not in q["topic"].lower()
            and topic.lower() not in q["topic_en"].lower()
        ):
            continue
        if status == "starred" and not q_with_status["starred"]:
            continue
        if status and status != "starred" and q_with_status["status"] != status:
            continue
        result.append(q_with_status)

    return result[:limit]


@app.get("/api/questions/{question_id}")
async def get_question(question_id: int):
    q = get_question_by_id(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM progress WHERE question_id = %s", (question_id,))
    prog = cur.fetchone()
    cur.close()
    conn.close()

    return {
        **q,
        "status": prog["status"] if prog else "unseen",
        "attempts": prog["attempts"] if prog else 0,
    }


@app.get("/api/topics")
async def get_topics():
    return get_all_topics()


@app.get("/api/topics/stats")
async def get_topics_stats():
    questions = load_questions()
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT question_id, status, starred FROM progress")
    progress = {row["question_id"]: row for row in cur.fetchall()}
    cur.close()
    conn.close()

    topics: dict = {}
    for q in questions:
        key = q["topic_en"]
        if key not in topics:
            topics[key] = {"topic": q["topic"], "topic_en": key,
                           "total": 0, "correct": 0, "wrong": 0, "starred": 0}
        topics[key]["total"] += 1
        prog = progress.get(q["id"], {})
        st = prog.get("status", "unseen") if prog else "unseen"
        if st in ("correct", "wrong"):
            topics[key][st] += 1
        if prog and prog.get("starred"):
            topics[key]["starred"] += 1

    return sorted(topics.values(), key=lambda t: -t["total"])


@app.get("/api/stats")
async def get_stats():
    questions = load_questions()
    total = len(questions)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT status, COUNT(*) as count FROM progress GROUP BY status")
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) as count FROM progress WHERE starred = TRUE")
    starred_count = cur.fetchone()["count"]
    cur.close()
    conn.close()

    stats = {"unseen": 0, "correct": 0, "wrong": 0, "starred": starred_count, "total": total}
    for row in rows:
        if row["status"] in stats:
            stats[row["status"]] = row["count"]
    stats["unseen"] = total - stats["correct"] - stats["wrong"]

    return stats


# ─── Progress API ─────────────────────────────────────────


class AnswerSubmit(BaseModel):
    question_id: int
    chosen_answers: List[str]  # now a list to support multiple correct answers


class StatusUpdate(BaseModel):
    question_id: int
    status: str

class AutovioToggle(BaseModel):
    question_id: int


@app.post("/api/answer")
async def submit_answer(body: AnswerSubmit):
    q = get_question_by_id(body.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    correct_ids = {a["id"] for a in q["answers"] if a["correct"]}
    chosen_ids = set(body.chosen_answers)
    is_correct = correct_ids == chosen_ids
    new_status = "correct" if is_correct else "wrong"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO progress (question_id, status, attempts, correct_count, last_seen)
        VALUES (%s, %s, 1, %s, NOW())
        ON CONFLICT (question_id) DO UPDATE SET
            status = EXCLUDED.status,
            attempts = progress.attempts + 1,
            correct_count = progress.correct_count + %s,
            last_seen = NOW()
    """,
        (body.question_id, new_status, 1 if is_correct else 0, 1 if is_correct else 0),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "correct": is_correct,
        "correct_answers": list(correct_ids),
        "chosen_answers": list(chosen_ids),
        "status": new_status,
    }


@app.post("/api/status")
async def update_status(body: StatusUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO progress (question_id, status)
        VALUES (%s, %s)
        ON CONFLICT (question_id) DO UPDATE SET status = EXCLUDED.status
    """,
        (body.question_id, body.status),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}


@app.post("/api/starred")
async def toggle_starred(body: AutovioToggle):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT starred FROM progress WHERE question_id = %s", (body.question_id,))
    row = cur.fetchone()
    new_val = not (row["starred"] if row else False)
    cur.execute(
        "INSERT INTO progress (question_id, starred) VALUES (%s, %s) ON CONFLICT (question_id) DO UPDATE SET starred = EXCLUDED.starred",
        (body.question_id, new_val),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"starred": new_val}


@app.post("/api/autovio")
async def toggle_autovio(body: AutovioToggle):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT autovio FROM progress WHERE question_id = %s", (body.question_id,))
    row = cur.fetchone()
    current = row["autovio"] if row else False
    new_val = not current
    cur.execute(
        """
        INSERT INTO progress (question_id, autovio)
        VALUES (%s, %s)
        ON CONFLICT (question_id) DO UPDATE SET autovio = EXCLUDED.autovio
        """,
        (body.question_id, new_val),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"autovio": new_val}


@app.delete("/api/progress")
async def reset_progress():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE progress SET status = 'unseen', attempts = 0, correct_count = 0")
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}


# ─── AI API ──────────────────────────────────────────────


class ExplainRequest(BaseModel):
    question_id: int
    chosen_answers: Optional[List[str]] = None
    language: Optional[str] = "en"


class ChatRequest(BaseModel):
    question_id: int
    message: str
    chosen_answers: Optional[List[str]] = None
    language: Optional[str] = "en"


@app.post("/api/explain")
async def explain(body: ExplainRequest):
    q = get_question_by_id(body.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    explanation = await explain_question(q, body.chosen_answers or [], body.language or "en")
    return {"explanation": explanation}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    q = get_question_by_id(body.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT role, message FROM chat_history
        WHERE question_id = %s ORDER BY created_at DESC LIMIT 6
    """,
        (body.question_id,),
    )
    history = list(reversed(cur.fetchall()))

    reply = await chat_about_question(q, body.message, history, body.chosen_answers, body.language or "en")

    cur.execute(
        "INSERT INTO chat_history (question_id, role, message) VALUES (%s, 'user', %s)",
        (body.question_id, body.message),
    )
    cur.execute(
        "INSERT INTO chat_history (question_id, role, message) VALUES (%s, 'assistant', %s)",
        (body.question_id, reply),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"reply": reply}


@app.delete("/api/chat/{question_id}")
async def clear_chat_history(question_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_history WHERE question_id = %s", (question_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}
