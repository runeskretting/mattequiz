import sqlite3
import uuid
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "mattequiz.db")


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
                login_token TEXT UNIQUE,
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

            CREATE TABLE IF NOT EXISTS invite_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL UNIQUE,
                used INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Migrasjon: legg til login_token-kolonne på eksisterende databaser
        try:
            conn.execute("ALTER TABLE users ADD COLUMN login_token TEXT UNIQUE")
        except Exception:
            pass  # Kolonnen finnes allerede

        # Migrasjon: generer token for brukere som mangler det (eksisterende brukere)
        for row in conn.execute("SELECT id FROM users WHERE login_token IS NULL").fetchall():
            conn.execute("UPDATE users SET login_token = ? WHERE id = ?",
                         (str(uuid.uuid4()), row["id"]))

        # Ensure "Anonym" user exists as fallback
        conn.execute(
            "INSERT OR IGNORE INTO users (name, login_token) VALUES ('Anonym', ?)",
            (str(uuid.uuid4()),)
        )


def create_user(name):
    """Oppretter ny bruker med login_token. Kaster ValueError hvis navn er tatt."""
    name = name.strip()
    if not name:
        raise ValueError("Navn kan ikke være tomt.")
    login_token = str(uuid.uuid4())
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, login_token) VALUES (?, ?)", (name, login_token)
            )
            return {"id": cursor.lastrowid, "name": name, "login_token": login_token}
        except sqlite3.IntegrityError:
            raise ValueError(f"Navnet '{name}' er allerede i bruk.")


def get_user_by_login_token(token):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, name, login_token FROM users WHERE login_token = ?", (token,)
        ).fetchone()
        return dict(row) if row else None


def get_user_login_token(name):
    """Brukes av manage.py for å hente en brukers innloggingslenke."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT login_token FROM users WHERE name = ?", (name,)
        ).fetchone()
        return row["login_token"] if row else None


def reset_user_login_token(name):
    """Genererer nytt login_token for en bruker. Returnerer nytt token, eller None hvis brukeren ikke finnes."""
    new_token = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE users SET login_token = ? WHERE name = ?", (new_token, name)
        )
        return new_token if cursor.rowcount > 0 else None


def create_invite_token():
    token = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute("INSERT INTO invite_tokens (token) VALUES (?)", (token,))
    return token


def get_invite_token(token):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invite_tokens WHERE token = ?", (token,)
        ).fetchone()
        return dict(row) if row else None


def mark_token_used(token):
    with get_db() as conn:
        conn.execute(
            "UPDATE invite_tokens SET used = 1 WHERE token = ?", (token,)
        )


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
