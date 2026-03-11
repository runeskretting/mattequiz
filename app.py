import json
import random
import os
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    jsonify,
)
from database import init_db, get_or_create_user, save_session, get_leaderboard, get_user_sessions

app = Flask(__name__)
app.secret_key = os.urandom(24)

TOTAL_QUESTIONS = 20


def generate_questions():
    questions = []
    ops = ["×", "+", "-", "÷"]
    for _ in range(TOTAL_QUESTIONS):
        op = random.choice(ops)
        if op == "×":
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            answer = a * b
        elif op == "+":
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            answer = a + b
        elif op == "-":
            a = random.randint(1, 20)
            b = random.randint(1, a)
            answer = a - b
        else:  # ÷
            a = random.randint(1, 20)
            divisors = [d for d in range(1, a + 1) if a % d == 0]
            b = random.choice(divisors)
            answer = a // b
        questions.append({"a": a, "b": b, "op": op, "answer": answer})
    return questions


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("quiz"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name", "").strip()
    if not name:
        return render_template("index.html", error="Skriv inn et navn.")
    try:
        user = get_or_create_user(name)
    except ValueError as e:
        return render_template("index.html", error=str(e))
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect(url_for("index"))
    questions = generate_questions()
    session["questions"] = questions
    return render_template("quiz.html", questions_json=json.dumps(questions))


@app.route("/submit", methods=["POST"])
def submit():
    if "user_id" not in session or "questions" not in session:
        return jsonify({"error": "Ikke innlogget"}), 401

    data = request.get_json()
    answers = data.get("answers", [])
    time_seconds = float(data.get("time_seconds", 0))

    questions = session["questions"]
    score = sum(
        1
        for i, q in enumerate(questions)
        if i < len(answers) and str(answers[i]).strip() == str(q["answer"])
    )
    mistakes = [
        {"a": q["a"], "b": q["b"], "op": q["op"], "correct": q["answer"], "given": answers[i]}
        for i, q in enumerate(questions)
        if i < len(answers) and str(answers[i]).strip() != str(q["answer"])
    ]

    save_session(session["user_id"], score, TOTAL_QUESTIONS, time_seconds)

    result = {
        "score": score,
        "total": TOTAL_QUESTIONS,
        "time_seconds": round(time_seconds, 1),
        "perfect": score == TOTAL_QUESTIONS,
        "mistakes": mistakes,
    }
    session["last_result"] = result

    return jsonify({"ok": True})


@app.route("/result")
def result():
    if "last_result" not in session:
        return redirect(url_for("index"))
    return render_template("result.html", result=session["last_result"])


@app.route("/leaderboard")
def leaderboard():
    entries = get_leaderboard()
    return render_template("leaderboard.html", entries=entries)


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("index"))
    sessions = get_user_sessions(session["user_id"])

    time_labels = []
    time_data = []
    score_labels = []
    score_data = []

    for s in sessions:
        date_str = s["played_at"][:10]
        score_labels.append(date_str)
        score_data.append(s["score"])
        if s["perfect"]:
            time_labels.append(date_str)
            time_data.append(round(s["time_seconds"], 1))

    return render_template(
        "profile.html",
        time_labels=json.dumps(time_labels),
        time_data=json.dumps(time_data),
        score_labels=json.dumps(score_labels),
        score_data=json.dumps(score_data),
        sessions=sessions,
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
