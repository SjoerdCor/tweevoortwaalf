""""The app to run Twee Voor Twaalf woordrader"""

import datetime
import os

import psycopg
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


@app.route("/taartpuzzel")
def paardensprong():
    """Page to play taartpuzzel"""
    return render_template("taartpuzzel.html")


@app.route("/new_game")
def new_game():
    """Start a new game"""
    playername = request.args.get("playername")

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

    database_url = os.getenv("DATABASE_URL")
    with psycopg.connect(database_url) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            query = """INSERT INTO woordrader.games (
                        start_time, answer, mode, playername
                        ) VALUES (
                    %s, %s, %s, %s
                    ) RETURNING game_id;"""
            cur.execute(
                query,
                (datetime.datetime.now(), twaalfletterwoord.answer, mode, playername),
            )
            gameid = cur.fetchone()[0]

            session["gameid"] = gameid

            letterplacement_dct = tuple(
                {
                    "game_id": gameid,
                    "position": k + 1,
                    "shown_letter": v["shown_letter"],
                    "correct": v["correct"],
                }
                for k, v in twaalfletterwoord.state.items()
            )
            cur.executemany(
                """INSERT INTO woordrader.shownletters (
                    game_id, position, shown_letter, correct
                ) VALUES (
                    %(game_id)s, %(position)s, %(shown_letter)s, %(correct)s
                )""",
                letterplacement_dct,
            )
            conn.commit()
    return redirect(url_for("index"))


@app.route("/buy_letter", methods=["POST"])
def buy_letter():
    """Handle buy letter request"""
    data = request.json
    quizposition = data.get("quizposition")
    session["game_state"][quizposition]["bought"] = True

    database_url = os.getenv("DATABASE_URL")

    with psycopg.connect(database_url) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            query = """INSERT INTO woordrader.boughtletters (
                        game_id, letterposition, buytime
                        ) VALUES (
                    %s, %s, %s
                    );"""
            cur.execute(
                query, (session["gameid"], quizposition, datetime.datetime.now())
            )

    return jsonify(session["game_state"])


@app.route("/guess", methods=["POST"])
def guess():
    """Handle a player guessing the end result"""
    data = request.json
    guess_input = data.get("guess")
    answer = session["answer"].lower()
    correct = guess_input.lower().strip().replace("ij", "\u0133") == answer
    result = "Correct" if correct else "Incorrect"
    result += f"! The correct answer is {answer!r}"

    database_url = os.getenv("DATABASE_URL")

    with psycopg.connect(database_url) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            query = """INSERT INTO woordrader.guesses (
                        game_id, guess_time, guess, correct
                        ) VALUES (
                    %s, %s, %s, %s
                    );"""
            cur.execute(
                query,
                (session["gameid"], datetime.datetime.now(), guess_input, correct),
            )

    session["game_active"] = False
    session["answer"] = None
    session["game_state"] = {}

    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(debug=True)
