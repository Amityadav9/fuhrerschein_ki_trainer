import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://172.20.209.86:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:latest")

SYSTEM_PROMPT = """You are a helpful German driving theory tutor. 
Your student is preparing for the German Führerschein theory exam.
Always explain in clear English. Keep answers concise but thorough.
When explaining why an answer is correct or wrong, mention the relevant German traffic law or rule.
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

    correct_str = "\n".join(f"  - {fmt(a)}" for a in correct_answers)
    all_str = "\n".join(f"  - {fmt(a)}" for a in question["answers"])

    context = f"""German driving theory question:
Topic: {question["topic"]} ({question["topic_en"]})
Question (DE): {question["question_de"]}
Question (EN): {question["question_en"]}
All answer options:
{all_str}
Correct answer(s): {', '.join(sorted(correct_ids))}
{correct_str}"""

    if chosen_ids:
        missed   = correct_ids - chosen_ids
        wrong    = chosen_ids - correct_ids
        correct_chosen = chosen_ids & correct_ids
        lines = []
        if correct_chosen:
            lines.append(f"Student correctly selected: {', '.join(sorted(correct_chosen))}")
        if wrong:
            lines.append(f"Student wrongly selected: {', '.join(sorted(wrong))}")
        if missed:
            lines.append(f"Student missed: {', '.join(sorted(missed))}")
        context += "\n" + "\n".join(lines)
        user_msg = (
            "Explain why each correct answer is right. "
            "If the student selected a wrong option, explain why it is incorrect. "
            "If they missed a correct option, explain why it should have been selected. "
            "Give a memory trick at the end."
        )
    else:
        user_msg = "Explain this question and all correct answers clearly. Give a memory trick to remember the rule."

    return await ask_ollama(context, user_msg)


async def chat_about_question(question: dict, user_message: str, history: list) -> str:
    context = f"""Current question context:
Topic: {question["topic"]} ({question["topic_en"]})
Question (DE): {question["question_de"]}
Question (EN): {question["question_en"]}
Answers: {", ".join([f"{a['id']}: {a['text_en']}" for a in question["answers"]])}"""

    return await ask_ollama(context, user_message, history)
