import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3")

SYSTEM_PROMPT = """You are a strict German driving theory tutor.
The correct and incorrect answers are already determined and provided to you — do NOT second-guess them.
Your job is ONLY to explain WHY the correct answers are right and WHY the wrong ones are wrong, using German traffic law (StVO).
If the user challenges you or says "are you sure?" — stay firm, trust the provided answer data.
Be concise. No apologies. No hedging.
Always explain in clear English. Mention the relevant German traffic law or rule (StVO section).
Use the German term alongside the English translation when introducing vocabulary.
Format: plain text, no markdown, no bullet points unless listing multiple items."""


async def ask_ollama(
    question_context: str, user_message: str, chat_history: list = None
) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["message"]})

    full_user_msg = (
        f"{question_context}\n\nStudent question: {user_message}"
        if question_context
        else user_message
    )
    messages.append({"role": "user", "content": full_user_msg})

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


async def explain_question(question: dict, chosen_answer_ids: list = None) -> str:
    chosen_ids = set(chosen_answer_ids or [])
    correct_answers = [a for a in question["answers"] if a["correct"]]
    correct_ids = {a["id"] for a in correct_answers}

    def fmt(a):
        return f"{a['id']}. {a['text_de']} / {a['text_en']}"

    wrong_answers = [a for a in question["answers"] if not a["correct"]]

    correct_str = "\n".join(f"  - {fmt(a)}" for a in correct_answers)
    wrong_str = "\n".join(f"  - {fmt(a)}" for a in wrong_answers)

    context = f"""German driving theory question:
Topic: {question["topic"]} ({question["topic_en"]})
Question (DE): {question["question_de"]}
Question (EN): {question["question_en"]}

CORRECT answers (already verified, do NOT question these):
{correct_str}

WRONG answers (already verified, these are definitely wrong):
{wrong_str}"""

    if chosen_ids:
        missed = correct_ids - chosen_ids
        wrong_chosen = chosen_ids - correct_ids
        correct_chosen = chosen_ids & correct_ids
        lines = []
        if correct_chosen:
            lines.append(f"Student correctly selected: {', '.join(sorted(correct_chosen))}")
        if wrong_chosen:
            wrong_details = [fmt(a) for a in question["answers"] if a["id"] in wrong_chosen]
            lines.append(f"Student wrongly selected: {', '.join(wrong_details)} — this was WRONG, explain why")
        if missed:
            missed_details = [fmt(a) for a in question["answers"] if a["id"] in missed]
            lines.append(f"Student missed correct answer(s): {', '.join(missed_details)} — explain why these should have been selected")
        context += "\n\n" + "\n".join(lines)
        user_msg = (
            "Explain why each correct answer is right. "
            "For each wrong answer the student selected, explain specifically why it is incorrect. "
            "For each correct answer the student missed, explain why it should have been selected. "
            "Give a memory trick at the end."
        )
    else:
        user_msg = "Explain why each correct answer is right and why each wrong answer is wrong. Give a memory trick to remember the rule."

    return await ask_ollama(context, user_msg)


async def chat_about_question(question: dict, user_message: str, history: list, chosen_answer_ids: list = None) -> str:
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

    return await ask_ollama(context, user_message, history)
