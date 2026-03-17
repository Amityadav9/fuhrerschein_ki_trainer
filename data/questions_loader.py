import json
import os
import httpx

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "questions.json")

SAMPLE_QUESTIONS = [
    {
        "id": 1,
        "topic": "Vorfahrt",
        "topic_en": "Right of way",
        "question_de": "Sie fahren auf einer Straße und nähern sich einer Kreuzung. Wer hat Vorfahrt?",
        "question_en": "You are driving on a road and approaching an intersection. Who has the right of way?",
        "answers": [
            {"id": "A", "text_de": "Fahrzeuge von rechts", "text_en": "Vehicles from the right", "correct": True},
            {"id": "B", "text_de": "Fahrzeuge von links", "text_en": "Vehicles from the left", "correct": False},
            {"id": "C", "text_de": "Fahrzeuge geradeaus", "text_en": "Vehicles going straight", "correct": False},
            {"id": "D", "text_de": "Das schnellste Fahrzeug", "text_en": "The fastest vehicle", "correct": False},
        ],
        "explanation_de": "Rechts vor links gilt an Kreuzungen ohne Vorfahrtszeichen.",
        "explanation_en": "Right before left applies at intersections without priority signs.",
        "points": 4,
        "image": None,
    },
    {
        "id": 2,
        "topic": "Geschwindigkeit",
        "topic_en": "Speed",
        "question_de": "Wie hoch ist die zulässige Höchstgeschwindigkeit innerhalb geschlossener Ortschaften?",
        "question_en": "What is the maximum permitted speed within built-up areas?",
        "answers": [
            {"id": "A", "text_de": "30 km/h", "text_en": "30 km/h", "correct": False},
            {"id": "B", "text_de": "50 km/h", "text_en": "50 km/h", "correct": True},
            {"id": "C", "text_de": "70 km/h", "text_en": "70 km/h", "correct": False},
            {"id": "D", "text_de": "100 km/h", "text_en": "100 km/h", "correct": False},
        ],
        "explanation_de": "Innerhalb geschlossener Ortschaften gilt eine Höchstgeschwindigkeit von 50 km/h.",
        "explanation_en": "Within built-up areas the maximum speed is 50 km/h unless otherwise signed.",
        "points": 4,
        "image": None,
    },
    {
        "id": 3,
        "topic": "Sicherheitsabstand",
        "topic_en": "Safe following distance",
        "question_de": "Welchen Mindestabstand müssen Sie bei 100 km/h zum vorausfahrenden Fahrzeug einhalten?",
        "question_en": "What minimum distance must you maintain at 100 km/h to the vehicle in front?",
        "answers": [
            {"id": "A", "text_de": "25 Meter", "text_en": "25 metres", "correct": False},
            {"id": "B", "text_de": "50 Meter", "text_en": "50 metres", "correct": True},
            {"id": "C", "text_de": "75 Meter", "text_en": "75 metres", "correct": False},
            {"id": "D", "text_de": "100 Meter", "text_en": "100 metres", "correct": False},
        ],
        "explanation_de": "Der Mindestabstand beträgt die Hälfte des Tachowertes in Metern: bei 100 km/h also 50 m.",
        "explanation_en": "The minimum distance is half the speedometer value in metres: at 100 km/h that is 50 m.",
        "points": 4,
        "image": None,
    },
    {
        "id": 4,
        "topic": "Alkohol",
        "topic_en": "Alcohol",
        "question_de": "Welcher Blutalkoholgehalt gilt für Fahranfänger in der Probezeit?",
        "question_en": "What blood alcohol limit applies to new drivers during probation?",
        "answers": [
            {"id": "A", "text_de": "0,0 Promille", "text_en": "0.0 ‰", "correct": True},
            {"id": "B", "text_de": "0,5 Promille", "text_en": "0.5 ‰", "correct": False},
            {"id": "C", "text_de": "0,3 Promille", "text_en": "0.3 ‰", "correct": False},
            {"id": "D", "text_de": "1,0 Promille", "text_en": "1.0 ‰", "correct": False},
        ],
        "explanation_de": "Fahranfänger und Fahrer unter 21 Jahren müssen absolut nüchtern fahren (0,0 Promille).",
        "explanation_en": "New drivers and drivers under 21 must have zero alcohol (0.0 ‰).",
        "points": 4,
        "image": None,
    },
    {
        "id": 5,
        "topic": "Überholverbot",
        "topic_en": "Overtaking ban",
        "question_de": "Wo ist das Überholen verboten?",
        "question_en": "Where is overtaking prohibited?",
        "answers": [
            {"id": "A", "text_de": "Auf Autobahnen", "text_en": "On motorways", "correct": False},
            {"id": "B", "text_de": "An unübersichtlichen Kurven", "text_en": "At blind bends", "correct": True},
            {"id": "C", "text_de": "Auf Landstraßen", "text_en": "On rural roads", "correct": False},
            {"id": "D", "text_de": "Bei Regen", "text_en": "In rain", "correct": False},
        ],
        "explanation_de": "An unübersichtlichen Kurven, Kuppen und Kreuzungen ist Überholen verboten.",
        "explanation_en": "Overtaking is prohibited at blind bends, crests, and intersections.",
        "points": 4,
        "image": None,
    },
    {
        "id": 6,
        "topic": "Autobahn",
        "topic_en": "Motorway",
        "question_de": "Welche Mindestgeschwindigkeit gilt auf der Autobahn?",
        "question_en": "What is the minimum speed on the motorway?",
        "answers": [
            {"id": "A", "text_de": "60 km/h", "text_en": "60 km/h", "correct": True},
            {"id": "B", "text_de": "80 km/h", "text_en": "80 km/h", "correct": False},
            {"id": "C", "text_de": "100 km/h", "text_en": "100 km/h", "correct": False},
            {"id": "D", "text_de": "Keine Mindestgeschwindigkeit", "text_en": "No minimum speed", "correct": False},
        ],
        "explanation_de": "Auf der Autobahn dürfen nur Fahrzeuge fahren, die bauartbedingt mindestens 60 km/h erreichen können.",
        "explanation_en": "Only vehicles capable of at least 60 km/h by design are allowed on the motorway.",
        "points": 4,
        "image": None,
    },
    {
        "id": 7,
        "topic": "Parken",
        "topic_en": "Parking",
        "question_de": "In welchem Abstand vor einem Feuerwehrzufahrtsschild darf nicht geparkt werden?",
        "question_en": "Within what distance of a fire brigade access sign is parking prohibited?",
        "answers": [
            {"id": "A", "text_de": "3 Meter", "text_en": "3 metres", "correct": False},
            {"id": "B", "text_de": "5 Meter", "text_en": "5 metres", "correct": True},
            {"id": "C", "text_de": "10 Meter", "text_en": "10 metres", "correct": False},
            {"id": "D", "text_de": "15 Meter", "text_en": "15 metres", "correct": False},
        ],
        "explanation_de": "Vor Feuerwehrzufahrten gilt beidseitig ein Parkverbot von 5 Metern.",
        "explanation_en": "Parking is prohibited within 5 metres on either side of fire brigade access signs.",
        "points": 4,
        "image": None,
    },
    {
        "id": 8,
        "topic": "Vorfahrt",
        "topic_en": "Right of way",
        "question_de": "Was bedeutet das Zeichen 'Vorfahrt gewähren'?",
        "question_en": "What does the 'give way' sign mean?",
        "answers": [
            {"id": "A", "text_de": "Sie haben Vorfahrt", "text_en": "You have right of way", "correct": False},
            {"id": "B", "text_de": "Sie müssen dem Querverkehr Vorfahrt gewähren", "text_en": "You must give way to crossing traffic", "correct": True},
            {"id": "C", "text_de": "Stopp und warten", "text_en": "Stop and wait", "correct": False},
            {"id": "D", "text_de": "Einfahrt verboten", "text_en": "No entry", "correct": False},
        ],
        "explanation_de": "Das Zeichen 205 bedeutet: Vorfahrt gewähren. Sie müssen den Querverkehr passieren lassen.",
        "explanation_en": "Sign 205 means: give way. You must let crossing traffic pass.",
        "points": 4,
        "image": None,
    },
]

def load_questions():
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return SAMPLE_QUESTIONS

def get_question_by_id(qid: int):
    questions = load_questions()
    for q in questions:
        if q["id"] == qid:
            return q
    return None

def get_questions_by_topic(topic: str):
    questions = load_questions()
    return [q for q in questions if topic.lower() in q["topic"].lower() or topic.lower() in q["topic_en"].lower()]

def get_all_topics():
    questions = load_questions()
    topics = {}
    for q in questions:
        key = q["topic"]
        if key not in topics:
            topics[key] = {"de": q["topic"], "en": q["topic_en"], "count": 0}
        topics[key]["count"] += 1
    return list(topics.values())

def get_total_count():
    return len(load_questions())
