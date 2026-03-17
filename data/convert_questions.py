import json

with open("data/questions_en.json", "r", encoding="utf-8") as f:
    en_questions = json.load(f)

with open("data/questions_de.json", "r", encoding="utf-8") as f:
    de_questions = json.load(f)

de_lookup = {q["question_id"]: q for q in de_questions}

SKIP_SUFFIXES = ['-M', '-C', '-CE', '-D', '-L', '-T']
SKIP_THEMES = {'Theme 2.8.'}

converted = []
answer_letters = ["A", "B", "C", "D"]
skipped = 0

for idx, en_q in enumerate(en_questions):
    # Filter to Klasse B only
    theme = en_q.get("theme_number", "")
    qid = en_q["question_id"]
    if theme in SKIP_THEMES or any(qid.endswith(s) for s in SKIP_SUFFIXES):
        skipped += 1
        continue

    de_q = de_lookup.get(qid, {})

    correct_letters = {
        a["letter"].replace(".", "").strip() for a in en_q.get("correct_answers", [])
    }

    en_options = en_q.get("options", [])
    if not en_options:  # image-choice questions — skip, can't render as buttons
        skipped += 1
        continue

    answers = []
    de_options = de_q.get("options", en_options)

    for i, en_opt in enumerate(en_options[:4]):
        letter = answer_letters[i]
        de_opt = de_options[i] if i < len(de_options) else en_opt
        is_correct = en_opt["letter"].replace(".", "").strip() in correct_letters
        answers.append(
            {
                "id": letter,
                "text_de": de_opt["text"],
                "text_en": en_opt["text"],
                "correct": is_correct,
            }
        )

    topic_en = en_q.get("theme_name", "General").title()
    topic_de = de_q.get("theme_name", topic_en)

    points_str = en_q.get("points", "4 Points")
    try:
        points = int(points_str.split()[0])
    except:
        points = 4

    # Image and video URLs
    image_url = en_q["image_urls"][0] if en_q.get("image_urls") else None
    video_url = en_q["video_urls"][0] if en_q.get("video_urls") else None

    converted.append(
        {
            "id": len(converted) + 1,
            "question_number": qid,
            "topic": topic_de,
            "topic_en": topic_en,
            "chapter": en_q.get("chapter_name", ""),
            "question_de": de_q.get("question_text", en_q["question_text"]),
            "question_en": en_q["question_text"],
            "answers": answers,
            "explanation_de": de_q.get("comment", ""),
            "explanation_en": en_q.get("comment", ""),
            "points": points,
            "image": image_url,
            "video": video_url,
        }
    )

with open("data/questions.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, ensure_ascii=False, indent=2)

print(f"Converted {len(converted)} Klasse B questions")
print(f"   Skipped {skipped} non-Klasse-B questions (truck/motorcycle/special)")
print(f"   Questions with images: {sum(1 for q in converted if q['image'])}")
print(f"   Questions with videos: {sum(1 for q in converted if q['video'])}")

topics = {}
for q in converted:
    t = q["topic_en"]
    topics[t] = topics.get(t, 0) + 1

print(f"\nTopics ({len(topics)} total):")
for t, count in sorted(topics.items(), key=lambda x: -x[1]):
    print(f"  {t}: {count} questions")
