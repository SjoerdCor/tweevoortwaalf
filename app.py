""""The app to run Twee Voor Twaalf woordrader"""

import datetime
import os

import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from tweevoortwaalf.paardensprong import Paardensprong
from tweevoortwaalf.taartpuzzel import Taartpuzzel
from tweevoortwaalf.woordrader import WoordRader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


def insert_data(table_name: str, data: dict, return_game_id=False) -> int | None:
    """Write data to the tweevoortwaalf database

    Parameters
    ----------
    table_name : str
        The name of the table (incl. schema) to which the data should be written
    data : dict
        Dictionary with column name as key and values as values of the dictionary
    return_game_id : bool
        Whether the game_id should be returned

    Returns
    -------
        game_id : Optional(int)
            when `return_game_id` is True, returns the game_id as integer;
            otherwise, returns None

    """
    database_url = os.getenv("DATABASE_URL")

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = tuple(data.values())

    query = f"INSERT INTO {table_name}.guesses ({columns}) VALUES ({placeholders})"
    if return_game_id:
        query += "RETURNING game_id"
    query += ";"

    with psycopg.connect(database_url) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(query, values)
            if return_game_id:
                result = cur.fetchone()[0]
                conn.commit()
                return result
            conn.commit()
            return None


@app.route("/")
def index():
    """Home page"""
    game_active = session.get("game_active", False)
    game_state = session.get("game_state", {})
    return render_template("index.html", state=game_state, active=game_active)


@app.route("/taartpuzzel")
def taartpuzzel():
    """Page to play taartpuzzel"""
    letters = session.get("taartpuzzelletters", [""] * 9)
    return render_template("taartpuzzel.html", letters=letters, result=None)


@app.route("/new_taartpuzzel")
def new_taartpuzzel():
    """Create a new paardensprong puzzle"""
    playername = request.args.get("playername")

    tp = Taartpuzzel()
    while not tp.unique_solution():
        tp.select_puzzle()
    session["taartpuzzelanswer"] = tp.answer
    session["taartpuzzelletters"] = tp.create_puzzle()

    data = {
        "start_time": datetime.datetime.now(),
        "answer": tp.answer,
        "startpoint": tp.startpoint,
        "missing_letter_index": tp.missing_letter_index,
        "playername": playername,
    }
    gameid = insert_data("taartpuzzel.games", data, return_game_id=True)
    session["taartpuzzelgameid"] = gameid
    return redirect(url_for("taartpuzzel"))


@app.route("/guess_taartpuzzel", methods=["POST"])
def guess_taartpuzzel():
    """Handle submitted guess for Taartpuzzel"""
    data = request.form
    guess_input = data.get("guess")
    answer = session["taartpuzzelanswer"].lower()
    correct = guess_input.lower().strip().replace("ij", "\u0133") == answer
    result = "Correct" if correct else "Incorrect"
    result += f"! The correct answer is {answer!r}"

    data = {
        "game_id": session["taartpuzzelgameid"],
        "guess_time": datetime.datetime.now(),
        "guess": guess_input,
        "correct": correct,
    }
    insert_data("taartpuzzel.guesses", data)
    return render_template(
        "taartpuzzel.html", letters=session["taartpuzzelletters"], result=result
    )


@app.route("/paardensprong")
def paardensprong():
    """Page to play taartpuzzel"""
    letters = session.get("paardensprongletters", [[""] * 3] * 3)
    return render_template("paardensprong.html", letters=letters, result=None)


@app.route("/new_paardensprong")
def new_paardensprong():
    """Create a new paardensprong puzzle"""
    playername = request.args.get("playername")

    ps = Paardensprong()
    while not ps.unique_solution():
        ps.select_puzzle()
    session["paardenspronganswer"] = ps.answer
    session["paardensprongletters"] = ps.create_puzzle()

    data = {
        "start_time": datetime.datetime.now(),
        "answer": ps.answer,
        "startpoint": ps.startpoint,
        "playername": playername,
    }
    gameid = insert_data("paardensprong.games", data, return_game_id=True)
    session["paardenspronggameid"] = gameid
    return redirect(url_for("paardensprong"))


@app.route("/guess_paardensprong", methods=["POST"])
def guess_paardensprong():
    """Handle submitted guess for Taartpuzzel"""
    data = request.form
    guess_input = data.get("guess")
    answer = session["paardenspronganswer"].lower()
    correct = guess_input.lower().strip().replace("ij", "\u0133") == answer
    result = "Correct" if correct else "Incorrect"
    result += f"! The correct answer is {answer!r}"

    data = {
        "game_id": session["paardenspronggameid"],
        "guess_time": datetime.datetime.now(),
        "guess": data.get("guess"),
        "correct": correct,
    }
    insert_data("paardensprong.guesses", data)

    return render_template(
        "paardensprong.html", letters=session["paardensprongletters"], result=result
    )


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

    data = {
        "game_id": session["gameid"],
        "letterposition": quizposition,
        "buytime": datetime.datetime.now(),
    }
    insert_data("woordrader.boughtletters", data)

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

    data = {
        "game_id": session["gameid"],
        "guess_time": datetime.datetime.now(),
        "guess": guess_input,
        "correct": correct,
    }
    insert_data("woordrader.guesses", data)

    session["game_active"] = False
    session["answer"] = None
    session["game_state"] = {}
    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(debug=True)
