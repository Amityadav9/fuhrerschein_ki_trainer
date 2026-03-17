# 🗺️ Roadmap — Führerschein AI Trainer

## Vision

Build the smartest driving theory practice tool that actually understands how you learn — not just a question bank, but a personal AI tutor that knows your weak spots, explains things in your language, and adapts to you over time.

> *"AutoVio gives you the questions. This app teaches you why."*

---

## ✅ Phase 1 — Done

- [x] 1989 Klasse B questions (bilingual DE + EN)
- [x] Checkbox answers — no hints on how many to select
- [x] Correct / wrong / missed answer highlighting
- [x] Star questions
- [x] Filter by status: All · Unseen · Wrong · Starred · Correct
- [x] Filter by type: Any · Video · Image · Text only · Multi-answer
- [x] Images inline (lazy loaded)
- [x] Videos inline
- [x] AI explanation on wrong answers (auto-opens, multi-answer aware)
- [x] Chat with AI per question
- [x] Progress saved to PostgreSQL
- [x] Wrong questions load fresh for retry (not pre-answered)
- [x] Reset all progress
- [x] Topic/lecture grouped view — AutoVio-style cards with per-topic progress bar
- [x] Random/shuffle mode per topic
- [x] One-click launch by topic: All / Random / Starred / Wrong

---

## 🔧 Phase 2 — Smart (next)

> Goal: app understands your weak areas and helps you focus

- [ ] **Exam mode** — 30 random questions, 45 min timer, pass/fail like the real test
- [ ] **Weak area detection** — after 50+ answers, show which topics you struggle with most
- [ ] **Smart queue** — prioritize questions you got wrong or haven't seen
- [ ] **Session summary** — after each session: X correct, Y wrong, top weak topics
- [ ] **Streak tracking** — daily practice streak

---

## 🧠 Phase 3 — Agentic + Memory (future)

> Goal: AI that remembers you and actively helps you improve

- [ ] **pgvector embeddings** — embed every wrong answer, find similar questions automatically
- [ ] **Pattern detection** — "You always confuse right-of-way at uncontrolled intersections"
- [ ] **Personalized AI system prompt** — AI gets briefed on your weak areas before each explanation
- [ ] **Spaced repetition** — resurface wrong questions at smart intervals (like Anki)
- [ ] **AI study plan** — given your exam date, AI generates a daily practice plan
- [ ] **Memory across sessions** — AI remembers what you struggled with last time

---

## 💡 Phase 4 — Polish (nice to have)

- [ ] **Mobile responsive** — works well on phone
- [ ] **Keyboard shortcuts** — A/B/C to select, Enter to submit
- [ ] **AI response streaming** — stream tokens in real time instead of waiting
- [ ] **Export progress** — PDF summary of weak areas
- [ ] **Dark/light mode toggle**

---

## Tech Upgrade Path

```
Now:     PostgreSQL + plain HTML
Phase 2: add progress analytics queries
Phase 3: PostgreSQL + pgvector — semantic question similarity
Phase 4: FastAPI WebSocket — real-time AI streaming
```

---

## Notes

- Dataset sourced from vyper0016/theorie-pruefung-trainer (clickclickdrive.de) — professional bilingual translations, not AI-generated
- pgvector already installed locally — Phase 3 needs no new infrastructure
- Ollama model is swappable via `.env` — `qwen3.5:latest` default, `gemma3:12b` also works well
- App is local-first by design — no cloud, no subscription, no data leaving your machine
