import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3")

SYSTEM_PROMPT_EN = """You are a strict German driving theory tutor.
LANGUAGE RULE: Respond in English only. Even if the question contains German text, your answer must be entirely in English. German words only allowed when citing a law (e.g. StVO) or introducing a term with its English translation.
CONTENT RULE: The CORRECT and WRONG answer labels are already determined and provided to you. They are authoritative — NEVER contradict them, NEVER override them with your own opinion. An answer labelled CORRECT is correct, full stop. An answer labelled WRONG is wrong, full stop. Your job is only to explain WHY, using German traffic law (StVO).
FORMAT RULE: Plain text only. No markdown. No ** bold **. No # headers. No bullet points with - or *. Write in paragraphs."""

SYSTEM_PROMPT_DE = """Du bist ein strenger Fahrlehrer für die deutsche Führerscheintheorie.
SPRACHREGEL: Antworte ausschließlich auf Deutsch.
INHALTSREGEL: Die RICHTIG und FALSCH Labels sind bereits bestimmt und verbindlich — widersprich ihnen NIEMALS. Eine als RICHTIG markierte Antwort ist richtig. Eine als FALSCH markierte Antwort ist falsch. Erkläre nur das WARUM, mit Bezug auf die StVO.
FORMATREGEL: Nur Fließtext. Kein Markdown. Kein ** Fett **. Keine # Überschriften. Keine Aufzählungszeichen. Schreibe in Absätzen."""


async def ask_ollama(
    question_context: str, user_message: str, chat_history: list = None, language: str = "en"
) -> str:
    prompt = SYSTEM_PROMPT_DE if language == "de" else SYSTEM_PROMPT_EN

    # Anchor question context in system message — model follows system prompt more reliably than user message
    lang_reminder = (
        "REMINDER: Your response must be in English only."
        if language != "de"
        else "ERINNERUNG: Antworte nur auf Deutsch."
    )
    if question_context:
        system_content = (
            f"{prompt}\n\n"
            "===QUESTION CONTEXT (answer ONLY about THIS question, nothing else)===\n"
            f"{question_context}\n"
            f"===\n{lang_reminder}"
        )
    else:
        system_content = prompt

    messages = [{"role": "system", "content": system_content}]

    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["message"]})

    messages.append({"role": "user", "content": user_message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2048,
                    },
                    "think": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        return "Could not connect to Ollama. Make sure Ollama is running: open a terminal and run 'ollama serve'"
    except Exception as e:
        return f"AI error: {str(e)}"


async def explain_question(question: dict, chosen_answer_ids: list = None, language: str = "en") -> str:
    chosen_ids = set(chosen_answer_ids or [])
    correct_answers = [a for a in question["answers"] if a["correct"]]

    def fmt(a):
        return f"{a['id']}. {a['text_de']} / {a['text_en']}"

    wrong_answers = [a for a in question["answers"] if not a["correct"]]

    # Label each answer explicitly inline so the model cannot miss the CORRECT/WRONG tag
    all_answers_labeled = "\n".join(
        f"  [{('CORRECT' if a['correct'] else 'WRONG')}] {fmt(a)}"
        for a in question["answers"]
    )

    correct_ids_str = ", ".join(a["id"] for a in correct_answers)
    wrong_ids_str = ", ".join(a["id"] for a in wrong_answers) or "none"

    context = f"""German driving theory question:
Topic: {question["topic"]} ({question["topic_en"]})
Question (DE): {question["question_de"]}
Question (EN): {question["question_en"]}

ANSWER KEY (official, authoritative — do NOT override these labels):
{all_answers_labeled}

Summary: CORRECT = {correct_ids_str} | WRONG = {wrong_ids_str}"""

    if chosen_ids:
        context += f"\n\nStudent chose: {', '.join(sorted(chosen_ids))}"
        user_msg = (
            "Go through every answer option:\n"
            "- For each CORRECT answer: explain WHY it is correct (StVO rule). Say whether the student chose it or missed it.\n"
            "- For each WRONG answer: explain WHY it is wrong. Say whether the student chose it.\n"
            "End with a memory trick."
        )
    else:
        user_msg = (
            "Go through every answer option:\n"
            "- For each CORRECT answer: explain WHY it is correct (StVO rule).\n"
            "- For each WRONG answer: explain WHY it is wrong.\n"
            "End with a memory trick."
        )

    return await ask_ollama(context, user_msg, language=language)





async def chat_about_question(question: dict, user_message: str, history: list, chosen_answer_ids: list = None, language: str = "en") -> str:
    correct_answers = [a for a in question["answers"] if a["correct"]]
    wrong_answers = [a for a in question["answers"] if not a["correct"]]
    correct_ids = {a["id"] for a in correct_answers}

    correct_str = ", ".join([f"{a['id']}: {a['text_en']}" for a in correct_answers])
    wrong_str = ", ".join([f"{a['id']}: {a['text_en']}" for a in wrong_answers])

    context = f"""Current question context:
Topic: {question["topic"]} ({question["topic_en"]})
Question (DE): {question["question_de"]}
Question (EN): {question["question_en"]}

CORRECT answers (already verified, do NOT question these): {correct_str}
WRONG answers (already verified, these are definitely wrong): {wrong_str}"""

    if chosen_answer_ids:
        chosen_ids = set(chosen_answer_ids)
        missed = correct_ids - chosen_ids
        wrong_chosen = chosen_ids - correct_ids
        correct_chosen = chosen_ids & correct_ids
        lines = []
        if correct_chosen:
            lines.append(f"Student correctly selected: {', '.join(sorted(correct_chosen))}")
        if wrong_chosen:
            lines.append(f"Student wrongly selected: {', '.join(sorted(wrong_chosen))}")
        if missed:
            lines.append(f"Student missed correct answer(s): {', '.join(sorted(missed))}")
        context += "\n\n" + "\n".join(lines)

    return await ask_ollama(context, user_message, history, language=language)
