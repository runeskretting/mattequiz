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
from database import (
    init_db, create_user, get_user_by_login_token, save_session,
    get_leaderboard, get_user_sessions,
    create_invite_token, get_invite_token, mark_token_used,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

init_db()

TOTAL_QUESTIONS = 20


def generate_questions():
    questions = []
    ops = ["×", "+", "-", "÷"]
    for _ in range(TOTAL_QUESTIONS):
        op = random.choice(ops)
        if op == "×":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
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
            a = random.randint(1, 10)
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


@app.route("/enter/<login_token>")
def enter(login_token):
    user = get_user_by_login_token(login_token)
    if not user:
        return render_template("index.html", error="Lenken er ugyldig. Sjekk at du bruker riktig lenke.")
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


@app.route("/register/<token>", methods=["GET", "POST"])
def register(token):
    token_row = get_invite_token(token)
    if not token_row or token_row["used"]:
        return render_template("register.html", error="Lenken er ugyldig eller allerede brukt.", token=None)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("register.html", error="Skriv inn et fornavn.", token=token)
        try:
            user = create_user(name)
        except ValueError as e:
            return render_template("register.html", error=str(e), token=token)
        mark_token_used(token)
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        base_url = request.host_url.rstrip("/")
        login_link = f"{base_url}/enter/{user['login_token']}"
        return render_template("register.html", login_link=login_link, user_name=user["name"])

    return render_template("register.html", token=token)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
