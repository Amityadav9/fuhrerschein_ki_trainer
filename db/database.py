import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL UNIQUE,
            status VARCHAR(20) DEFAULT 'unseen',  -- unseen, correct, wrong, starred
            attempts INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            last_seen TIMESTAMP DEFAULT NOW(),
            notes TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL,
            role VARCHAR(10) NOT NULL,  -- user, assistant
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            started_at TIMESTAMP DEFAULT NOW(),
            ended_at TIMESTAMP,
            questions_seen INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0,
            wrong INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database tables ready")
