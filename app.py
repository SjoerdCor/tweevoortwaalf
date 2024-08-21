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

    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
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


def clean_str(strng: str) -> str:
    """Make strings comparable"""
    return strng.lower().strip().replace("ij", "\u0133")


def is_guess_correct(guess: str, answer: str) -> bool:
    """Check whether the guess is correct

    Cleans both guess and answer first
    """
    return clean_str(guess) == clean_str(answer)


@app.route("/woordrader")
def woordrader():
    """Home page"""
    game_active = session.get("game_active", False)
    game_state = session.get("game_state", {})
    return render_template(
        "woordrader.html",
        letters=game_state,
        active=game_active,
        guess_correct=None,
        answer=None,
    )


@app.route("/taartpuzzel")
def taartpuzzel():
    """Page to play taartpuzzel"""
    letters = session["taartpuzzel"].get("letters", [""] * 9)
    return render_template(
        "taartpuzzel.html", letters=letters, guess_correct=None, answer=None
    )


@app.route("/paardensprong")
def paardensprong():
    """Page to play taartpuzzel"""
    letters = session["paardensprong"].get("letters", [[""] * 3] * 3)
    return render_template(
        "paardensprong.html", letters=letters, guess_correct=None, answer=None
    )


def new_puzzle(puzzlename, puzzleclass):
    """Base function for creating a new puzzle"""
    playername = request.args.get("playername")

    puzzle = puzzleclass()
    while not puzzle.unique_solution():
        puzzle.select_puzzle()

    data = puzzle.__dict__.copy()
    # Not known at creation yet, so don't write
    to_eliminate = {"guesstime", "guess", "correct"}
    for item in to_eliminate:
        data.pop(item, None)
    data["playername"] = playername

    gameid = insert_data(f"{puzzlename}.games", data, return_game_id=True)

    session[puzzlename] = {}
    session[puzzlename]["answer"] = puzzle.answer
    session[puzzlename]["letters"] = puzzle.create_puzzle()
    session[puzzlename]["gameid"] = gameid

    return redirect(url_for(puzzlename))


@app.route("/new_taartpuzzel")
def new_taartpuzzel():
    """Create a new taartpuzzel"""
    return new_puzzle("taartpuzzel", Taartpuzzel)


@app.route("/new_paardensprong")
def new_paardensprong():
    """Create a new taartpuzzel"""
    return new_puzzle("paardensprong", Paardensprong)


def handle_guess(puzzlename):
    """Base function for handling submitted guesses"""
    guess_input = request.form.get("guess")
    answer = session[puzzlename]["answer"]
    correct = is_guess_correct(guess_input, answer)
    data = {
        "game_id": session[puzzlename]["gameid"],
        "guess_time": datetime.datetime.now(),
        "guess": guess_input,
        "correct": correct,
    }
    insert_data(f"{puzzlename}.guesses", data)
    return render_template(
        f"{puzzlename}.html",
        letters=session[puzzlename]["letters"],
        guess_correct=correct,
        answer=answer,
    )


@app.route("/guess_woordrader", methods=["POST"])
def guess_woordrader():
    """Handle submitted guess for Woordrader"""
    return handle_guess("woordrader")


@app.route("/guess_taartpuzzel", methods=["POST"])
def guess_taartpuzzel():
    """Handle submitted guess for Taartpuzzel"""
    return handle_guess("taartpuzzel")


@app.route("/guess_paardensprong", methods=["POST"])
def guess_paardensprong():
    """Handle submitted guess for Paardensprong"""
    return handle_guess("paardensprong")


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
    return redirect(url_for("woordrader"))


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


if __name__ == "__main__":
    app.run(debug=True)
