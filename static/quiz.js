(function () {
  const questions = QUESTIONS;
  let current = 0;
  let userAnswers = [];
  let startTime = null;
  let timerInterval = null;

  const questionEl = document.getElementById("question");
  const answerInput = document.getElementById("answer-input");
  const submitBtn = document.getElementById("submit-btn");
  const progressEl = document.getElementById("progress");
  const timerEl = document.getElementById("timer");
  const feedbackEl = document.getElementById("feedback");

  function showQuestion(index) {
    const q = questions[index];
    questionEl.textContent = `${q.a} ${q.op} ${q.b} = ?`;
    progressEl.textContent = `Spørsmål ${index + 1} av ${questions.length}`;
    answerInput.value = "";
    feedbackEl.textContent = "";
    feedbackEl.className = "answer-feedback";
    answerInput.focus();
  }

  function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      timerEl.textContent = elapsed.toFixed(1) + "s";
    }, 100);
  }

  function stopTimer() {
    clearInterval(timerInterval);
    return (Date.now() - startTime) / 1000;
  }

  function submitAnswer() {
    const raw = answerInput.value.trim();
    if (raw === "") return;

    const answer = raw;
    const correctAnswer = questions[current].answer;
    userAnswers.push(answer);

    if (String(answer) !== String(correctAnswer)) {
      feedbackEl.textContent = `Feil! Riktig svar er ${correctAnswer}`;
      feedbackEl.className = "answer-feedback feedback-wrong";
    } else {
      feedbackEl.textContent = "Riktig!";
      feedbackEl.className = "answer-feedback feedback-correct";
    }

    current++;
    if (current < questions.length) {
      showQuestion(current);
    } else {
      finishQuiz();
    }
  }

  async function finishQuiz() {
    const timeSeconds = stopTimer();
    answerInput.disabled = true;
    submitBtn.disabled = true;
    feedbackEl.textContent = "Sender inn svar...";

    try {
      const resp = await fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: userAnswers, time_seconds: timeSeconds }),
      });

      if (resp.ok) {
        window.location.href = "/result";
      } else {
        feedbackEl.textContent = "Noe gikk galt. Prøv igjen.";
        feedbackEl.className = "answer-feedback feedback-wrong";
      }
    } catch (e) {
      feedbackEl.textContent = "Noe gikk galt. Prøv igjen.";
      feedbackEl.className = "answer-feedback feedback-wrong";
    }
  }

  // Event listeners
  submitBtn.addEventListener("click", submitAnswer);

  answerInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submitAnswer();
    }
  });

  // Start
  showQuestion(0);
  startTimer();
})();
