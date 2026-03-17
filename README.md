# Führerschein AI Trainer

A local, private German driving theory practice app with AI explanations — built as a smarter alternative to AutoVio.

## What this does differently

AutoVio explains answers with a single static line. This app adds:

- **AI explanation on every question** — deep explanation of every correct/wrong answer, the rule behind it, memory trick
- **Chat with AI** — ask follow-ups like "why not B?" or "explain in simple English"
- **Bilingual DE + EN** — question and answers shown in both languages side by side
- **100% local and private** — runs on your machine, AI via Ollama, no cloud, no paid APIs

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + Python |
| AI | Ollama (`qwen3` 8.2B) — local, free |
| Database | PostgreSQL |
| Frontend | Plain HTML + CSS (no build step) |
| Package manager | `uv` |

## Setup

### 1. Install dependencies
```bash
uv sync
```

### 2. Configure environment
```bash
cp .env.example .env
```
Edit `.env` with your Postgres credentials and Ollama URL.

### 3. Start Ollama
```bash
ollama pull qwen3
ollama serve
```

> **Why `qwen3`?** We tested `qwen3.5:latest`, `llama3.2:3b`, and `qwen3`. Smaller models (3B) hallucinate answers — they ignore the provided correct/wrong labels and make up their own. `qwen3` (8.2B params, Q4_K_M quantized, ~5.2GB) follows system prompts reliably, supports thinking mode for better reasoning, and has strong multilingual support for German/English driving theory explanations.

### 4. Run
```bash
uvicorn main:app --reload
```

Open `http://localhost:8000`

## Question Dataset

1989 Klasse B questions sourced from [vyper0016/theorie-pruefung-trainer](https://github.com/vyper0016/theorie-pruefung-trainer) — bilingual DE + EN, images and videos included.

`data/questions.json` is included in the repo — no conversion step needed.

## Database

Tables created automatically on first run:
- `progress` — status per question (correct / wrong / starred)
- `chat_history` — AI conversation history per question

View your data anytime in pgAdmin or DBeaver.

## Features

### Practice
- 1989 Klasse B questions — bilingual DE + EN
- Multi-answer questions (select all that apply)
- Images and videos embedded inline
- Wrong answer → AI auto-explains immediately (aware of which answers you got right/wrong/missed)
- Correct questions lock with answers shown; wrong questions stay fresh to retry

### Navigation
- **Home** — overall progress stats + topic quick-links
- **Topics** (`/topics`) — AutoVio-style topic cards with per-topic progress bar and one-click launch (All / Random / Starred / Wrong per topic)
- **Practice** (`/practice`) — full question list

### Filters
- By status: All · Unseen · Wrong · Starred · Correct
- By type: Any · Video · Image · Text only · Multi-answer
- Reset all progress with one click

### AI
- **Explain** — explains every correct and wrong answer with the relevant German traffic law + memory trick
- **Chat** — ask follow-up questions per question
- Fully context-aware for multi-answer questions
- Chat knows which answers you selected — can tell you what you missed and why
