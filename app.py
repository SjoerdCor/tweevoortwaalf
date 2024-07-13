""""The app to run Twee Voor Twaalf woordrader"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

from tweevoortwaalf.woordrader import WoordRader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


@app.route("/")
def index():
    """Home page"""
    if "game_state" not in session:
        twaalfletterwoord = WoordRader()
        session["game_state"] = twaalfletterwoord.state
        session["answer"] = twaalfletterwoord.answer
    return render_template("index.html", state=session["game_state"])


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
    return jsonify({"result": result})


@app.route("/play_again", methods=["POST"])
def play_again():
    """Set up a new round"""
    session.pop("game_state", None)
    session.pop("answer", None)
    return jsonify({"message": "Game reset."})


if __name__ == "__main__":
    app.run(debug=True)
