""""The app to run Twee Voor Twaalf woordrader"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from tweevoortwaalf.woordrader import WoordRader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


@app.route("/")
def index():
    """Home page"""
    game_active = session.get("game_active", False)
    game_state = session.get("game_state", {})
    return render_template("index.html", state=game_state, active=game_active)


@app.route("/new_game")
def new_game():
    """Start a new game"""
    mode = request.args.get("mode", "normal")
    if mode == "easy":
        p_wrong = 0
    elif mode == "normal":
        p_wrong = 0.05
    else:
        raise ValueError(f"Unknown mode {mode!r}")
    twaalfletterwoord = WoordRader(p_unknown=p_wrong, p_wrong=p_wrong)
    twaalfletterwoord.initialize_game()
    session["game_state"] = twaalfletterwoord.state
    session["answer"] = twaalfletterwoord.answer
    session["game_active"] = True
    session["mode"] = mode

    return redirect(url_for("index"))


@app.route("/buy_letter", methods=["POST"])
def buy_letter():
    """Handle buy letter request"""
    data = request.json
    quizposition = data.get("quizposition")
    session["game_state"][quizposition]["bought"] = True
    return jsonify(session["game_state"])


@app.route("/guess", methods=["POST"])
def guess():
    """Handle a player guessing the end result"""
    data = request.json
    guess_input = data.get("guess")
    answer = session["answer"].lower()
    result = (
        "Correct"
        if guess_input.lower().strip().replace("ij", "\u0133") == answer
        else "Incorrect"
    )
    result += f"! The correct answer is {answer!r}"

    session["game_active"] = False
    session["answer"] = None
    session["game_state"] = {}

    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(debug=True)
