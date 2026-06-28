import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "provenance.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                content_id  TEXT PRIMARY KEY,
                creator_id  TEXT,
                timestamp   TEXT,
                attribution TEXT,
                confidence  REAL,
                llm_score   REAL,
                stylo_score REAL,
                status      TEXT DEFAULT 'classified'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appeals (
                appeal_id            TEXT PRIMARY KEY,
                content_id           TEXT,
                creator_reasoning    TEXT,
                appeal_timestamp     TEXT,
                original_confidence  REAL,
                original_attribution TEXT
            )
        """)
        conn.commit()


def log_submission(content_id, creator_id, timestamp, attribution, confidence, llm_score, stylo_score):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO submissions
                (content_id, creator_id, timestamp, attribution, confidence, llm_score, stylo_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'classified')
            """,
            (content_id, creator_id, timestamp, attribution, confidence, llm_score, stylo_score),
        )
        conn.commit()


def get_submission(content_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM submissions WHERE content_id = ?",
            (content_id,),
        ).fetchone()
    return dict(row) if row else None


def set_status_under_review(content_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE submissions SET status = 'under_review' WHERE content_id = ?",
            (content_id,),
        )
        conn.commit()


def log_appeal(appeal_id, content_id, creator_reasoning, appeal_timestamp, original_confidence, original_attribution):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO appeals
                (appeal_id, content_id, creator_reasoning, appeal_timestamp, original_confidence, original_attribution)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (appeal_id, content_id, creator_reasoning, appeal_timestamp, original_confidence, original_attribution),
        )
        conn.commit()


def get_recent_logs(limit=10):
    with get_connection() as conn:
        submissions = conn.execute(
            "SELECT * FROM submissions ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        appeals = conn.execute(
            "SELECT * FROM appeals ORDER BY appeal_timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {
        "submissions": [dict(r) for r in submissions],
        "appeals": [dict(r) for r in appeals],
    }
