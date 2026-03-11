import sqlite3
from contextlib import contextmanager

DB_PATH = "mattequiz.db"
MAX_USERS = 4


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL DEFAULT 20,
                time_seconds REAL NOT NULL,
                perfect INTEGER NOT NULL DEFAULT 0,
                played_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_perfect
                ON sessions(perfect, time_seconds);
        """)
        # Ensure "Anonym" user exists as fallback
        conn.execute(
            "INSERT OR IGNORE INTO users (name) VALUES ('Anonym')"
        )


def get_or_create_user(name):
    name = name.strip()
    if not name:
        raise ValueError("Navn kan ikke være tomt.")

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, name FROM users WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            return dict(existing)

        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count >= MAX_USERS:
            raise ValueError(
                f"Maks {MAX_USERS} brukere er nådd. Kan ikke opprette ny bruker."
            )

        cursor = conn.execute(
            "INSERT INTO users (name) VALUES (?)", (name,)
        )
        return {"id": cursor.lastrowid, "name": name}


def save_session(user_id, score, total, time_seconds):
    perfect = 1 if score == total else 0
    with get_db() as conn:
        conn.execute(
            """INSERT INTO sessions (user_id, score, total_questions, time_seconds, perfect)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, score, total, time_seconds, perfect),
        )


def get_leaderboard():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT u.name, s.score, s.total_questions, s.time_seconds, s.played_at
               FROM sessions s
               JOIN users u ON u.id = s.user_id
               WHERE s.perfect = 1
               ORDER BY s.time_seconds ASC
               LIMIT 10"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_user_sessions(user_id):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT score, total_questions, time_seconds, perfect, played_at
               FROM sessions
               WHERE user_id = ?
               ORDER BY played_at ASC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
