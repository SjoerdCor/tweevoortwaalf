""""The app to run Twee Voor Twaalf woordrader"""

import datetime
import logging
import os

import pandas as pd
import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from sqlalchemy import create_engine

from tweevoortwaalf.paardensprong import Paardensprong
from tweevoortwaalf.taartpuzzel import Taartpuzzel
from tweevoortwaalf.woordrader import WoordRader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


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


def probability_option(p: float, n: float) -> float:
    """Get weights, to select options with probability closest to 50%

    Parameters
    ----------
    p : float
        The probability of getting the answer right
    n : float
        Power: Higher values make values far from 50% less likely to select
    """
    return (p - p**2) ** n


def clean_str(strng: str) -> str:
    """Make strings comparable"""
    return strng.lower().strip().replace("ij", "\u0133")


def is_guess_correct(guess: str, answer: str) -> bool:
    """Check whether the guess is correct

    Cleans both guess and answer first
    """
    return clean_str(guess) == clean_str(answer)


@app.route("/")
def home():
    """Home page"""
    return render_template("index.html")


@app.route("/woordrader")
def woordrader():
    """Home page"""
    # active = session.get("woordrader", {}).get("active", False)
    # state = session.get("woordrader", {}).get("state", WoordRader().state)
    state = WoordRader().state
    active = False
    return render_template(
        "woordrader.html",
        state=state,
        active=active,
        guess_correct=None,
        answer=None,
    )


@app.route("/taartpuzzel")
def taartpuzzel():
    """Page to play taartpuzzel"""
    state = session.get("taartpuzzel", {}).get("state", [""] * 9)
    return render_template(
        "taartpuzzel.html", state=state, guess_correct=None, answer=None
    )


@app.route("/paardensprong")
def paardensprong():
    """Page to play taartpuzzel"""
    state = session.get("paardensprong", {}).get("state", [[""] * 3] * 3)
    return render_template(
        "paardensprong.html", state=state, guess_correct=None, answer=None
    )


def new_puzzle(puzzlename, puzzleclass, **kwargs):
    """Base function for creating a new puzzle"""
    playername = request.json.get("playername")

    puzzle = puzzleclass(**kwargs)
    while not puzzle.unique_solution():
        puzzle.select_puzzle()

    puzzle.start_time = datetime.datetime.now()
    data = puzzle.__dict__.copy()
    # Not known at creation yet, so don't write
    to_eliminate = {"guesstime", "guess", "correct"}
    for item in to_eliminate:
        data.pop(item, None)

    # Since the state for woordrader is more complex, this is written to a
    # different table, for normalized tables
    if puzzlename == "woordrader":
        data.pop("state", None)

    data["playername"] = playername

    gameid = insert_data(f"{puzzlename}.games", data, return_game_id=True)

    session[puzzlename] = {}
    session[puzzlename]["answer"] = puzzle.answer
    session[puzzlename]["state"] = puzzle.create_puzzle()
    session[puzzlename]["gameid"] = gameid
    session[puzzlename]["active"] = True

    html = render_template(
        f"{puzzlename}specific.html", state=session[puzzlename]["state"], active=True
    )
    return jsonify({"html": html})


@app.route("/new_woordrader", methods=["POST"])
def new_woordrader():
    """Create a new Woordrader puzzle"""
    mode = request.json.get("mode", "normal")
    if mode == "easy":
        p_wrong = 0
        p_unknown = 0
    elif mode == "normal":
        p_wrong = 0.05
        p_unknown = 0.05
    else:
        raise ValueError(f"Unknown mode {mode!r}")

    response = new_puzzle(
        "woordrader", WoordRader, p_wrong=p_wrong, p_unknown=p_unknown
    )

    database_url = os.getenv("DATABASE_URL")
    with psycopg.connect(database_url) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            letterplacements = tuple(
                {
                    "game_id": session["woordrader"]["gameid"],
                    "position": k + 1,
                    "shown_letter": v["shown_letter"],
                    "correct": v["correct"],
                }
                for k, v in session["woordrader"]["state"].items()
            )
            cur.executemany(
                """INSERT INTO woordrader.shownletters (
                    game_id, position, shown_letter, correct
                ) VALUES (
                    %(game_id)s, %(position)s, %(shown_letter)s, %(correct)s
                )""",
                letterplacements,
            )
            conn.commit()
    return response


def select_hard_puzzle(name: str) -> dict:
    """Select a puzzle based on probability of getting it wrong"""
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url.replace("postgresql", "postgresql+psycopg"))
    with engine.connect() as conn:
        puzzleoptions = pd.read_sql_table("puzzleoptions", con=conn, schema=name)

    p = probability_option(puzzleoptions["probability"], n=10)
    chosen_puzzle = puzzleoptions.sample(weights=p).squeeze()
    logger.debug(p[puzzleoptions["answer"] == chosen_puzzle["answer"]])
    logger.debug(puzzleoptions[puzzleoptions["answer"] == chosen_puzzle["answer"]])
    kwargs = {
        "answer": chosen_puzzle["answer"],
        "direction": chosen_puzzle["direction"],
        "startpoint": chosen_puzzle["startpoint"],
    }
    logger.info(kwargs)
    # For now, this word will not be played again until there is a full rerun of predictions
    # Its a bit harsh, but good enough
    # TODO: This should actually be done at submit, but that's slightly harder to implement
    # And does not seem worth the trouble for now
    # pylint: disable=not-context-manager
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            query = f"""
                    UPDATE {name}.puzzleoptions
                    SET "NTimesWordSeenBefore" = "NTimesWordSeenBefore" + 1,
                        probability = NULL
                    WHERE answer = %s;
            """
            cur.execute(query, (chosen_puzzle["answer"],))
            conn.commit()
    return kwargs


@app.route("/new_taartpuzzel", methods=["POST"])
def new_taartpuzzel():
    """Create a new taartpuzzel"""
    mode = request.json.get("mode", "normal")
    logger.info("New taartpuzzel with mode %s", (mode))
    if mode == "normal":
        kwargs = {}
    elif mode == "hard":
        kwargs = select_hard_puzzle("taartpuzzel")
    else:
        raise ValueError(f"Unknown mode {mode!r}")
    return new_puzzle("taartpuzzel", Taartpuzzel, **kwargs)


@app.route("/new_paardensprong", methods=["POST"])
def new_paardensprong():
    """Create a new taartpuzzel"""

    mode = request.json.get("mode", "normal")
    if mode == "normal":
        kwargs = {}
    elif mode == "hard":
        kwargs = select_hard_puzzle("paardensprong")
    else:
        raise ValueError(f"Unknown mode {mode!r}")
    return new_puzzle("paardensprong", Paardensprong, **kwargs)


def handle_guess(puzzlename):
    """Base function for handling submitted guesses"""
    guess_input = request.json.get("guess")
    answer = session[puzzlename]["answer"]
    correct = is_guess_correct(guess_input, answer)
    data = {
        "game_id": session[puzzlename]["gameid"],
        "guess_time": datetime.datetime.now(),
        "guess": guess_input,
        "correct": correct,
    }
    insert_data(f"{puzzlename}.guesses", data)

    session[puzzlename]["active"] = False
    return jsonify({"answer": answer, "correct": correct})


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


@app.route("/buy_letter", methods=["POST"])
def buy_letter():
    """Handle buy letter request"""
    data = request.json
    quizposition = data.get("quizposition")
    session["woordrader"]["state"][quizposition]["bought"] = True

    data = {
        "game_id": session["woordrader"]["gameid"],
        "letterposition": quizposition,
        "buytime": datetime.datetime.now(),
    }
    insert_data("woordrader.boughtletters", data)

    return jsonify(session["woordrader"]["state"])


if __name__ == "__main__":
    app.run(debug=True)
