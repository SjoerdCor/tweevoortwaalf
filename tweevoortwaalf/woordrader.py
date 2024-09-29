"""Class to play the woordrader game from twee voor twaalf"""

import csv
import datetime
import importlib
import os
import random
from typing import List, Tuple

import pandas as pd

LETTER_OCCURENCE_FIRST_POSITION = {  # based on words of all length
    "b": 0.09775666589860389,
    "s": 0.08800817691439645,
    "k": 0.0707917545507719,
    "v": 0.06328837212050314,
    "a": 0.05666530778638402,
    "g": 0.05500511057149778,
    "m": 0.05450291568443255,
    "p": 0.051217970305511736,
    "d": 0.04955186491548356,
    "o": 0.04610149063258831,
    "h": 0.044588997796250675,
    "t": 0.04389183312950129,
    "l": 0.040642336801432144,
    "r": 0.03712106441683357,
    "c": 0.03528953012283096,
    "w": 0.03527771377254707,
    "i": 0.024229426257111965,
    "z": 0.024229426257111965,
    "e": 0.023768588596040342,
    "f": 0.023124597505568455,
    "n": 0.015668480476435244,
    "j": 0.008690925633799489,
    "u": 0.007751525786230407,
    "ij": 0.0017724525425831723,
    "q": 0.0005730929887685591,
    "y": 0.0002895005819552515,
    "x": 0.00020087795482609286,
}


class WoordRader:
    """Class to play the woordrader game from twee voor twaalf"""

    n_letters = 12

    def __init__(self, answer=None, p_wrong=0.05, p_unknown=0.05):
        if not isinstance(answer, str):
            raise TypeError(f"Answer must be of class `str`, not {type(answer)}")
        if len(answer) != 12:
            raise ValueError(f"Answer must have length 12, untrue for {answer}")
        self.answer = answer
        if self.answer is None:
            self.state = {
                i: {
                    "shown_letter": "",
                    "answer_position": i,
                    "bought": False,
                    "correct": True,
                    "true_letter": "",
                }
                for i in range(12)
            }
        else:
            self._generate_starting_position()

        if p_wrong > 1 or p_wrong < 0:
            raise ValueError(f"p_wrong must be between 0 and 1, not {p_wrong}")
        self.p_wrong = p_wrong
        if p_unknown > 1 or p_unknown < 0:
            raise ValueError(f"p_unknown must be between 0 and 1, not {p_unknown}")
        if p_unknown + p_wrong > 1:
            raise ValueError(
                f"p_unknown and p_wrong must add to 1 at max: {p_unknown}, {p_wrong}"
            )
        self.p_unknown = p_unknown

        self.guess = None
        self.start_time = None
        self.guesstime = None

    def select_puzzle(self):
        """Choose a new word to play"""
        data_path = importlib.resources.files("tweevoortwaalf.Data").joinpath(
            f"suitable_{self.n_letters}_letter_words.txt"
        )
        wordlist = pd.read_csv(data_path).squeeze()

        self.answer = wordlist.sample(1).squeeze()
        self.start_time = datetime.datetime.now()

    def _generate_starting_position(self):
        state = {}

        quizpositions = random.sample(range(self.n_letters), self.n_letters)
        for answer_position, (letter, quizposition) in enumerate(
            zip(self.answer, quizpositions)
        ):
            random_nr = random.random()
            if random_nr < self.p_wrong:
                shown_letter = random.choices(
                    list(LETTER_OCCURENCE_FIRST_POSITION.keys()),
                    list(LETTER_OCCURENCE_FIRST_POSITION.values()),
                )[0]
                correct = False
            elif self.p_wrong < random_nr < self.p_wrong + self.p_unknown:
                shown_letter = "-"
                correct = False
            else:
                shown_letter = letter
                correct = True
            state[quizposition] = {
                "shown_letter": shown_letter,
                "answer_position": answer_position,
                "bought": False,
                "correct": correct,
                "true_letter": letter,
            }
        self.state = state

    def create_puzzle(self):
        """Set up a new round of the anagram game"""
        self._generate_starting_position()
        return self.state

    def unique_solution(self):
        """Determing whether the woordrader anagram is unique"""
        return self.answer is not None  # TODO: implement by checking for anagrams

    def get_bottom_row(self) -> List[str]:
        """Calculate what to show on the bottom row

        Correct, bought letters in the right place, correct, wrong letters show
        up as "?", and empty string if the letter is not bought

        Returns
        -------
        List[str]
            the twelve positions and what must be shown on each position
        """
        by_answeringposition = dict(
            sorted(self.state.items(), key=lambda item: item[1]["answer_position"])
        )

        bottom_row = []
        for _, state in by_answeringposition.items():
            if state["bought"]:
                if state["correct"]:
                    bottom_row.append(state["true_letter"])
                else:
                    bottom_row.append("?")
            else:
                bottom_row.append("")
        return bottom_row

    def get_top_row(self) -> List[str]:
        """Get what to show for the top row

        (Possibly incorrect) letters which are not bought, empty strings if the letter
        is bought

        Returns
        -------
        List[str]
            The twelve positions
        """
        by_quizposition = dict(sorted(self.state.items()))
        top_row = [
            state["shown_letter"] if not state["bought"] else ""
            for _, state in by_quizposition.items()
        ]
        return top_row

    def show_guess_panel(self):
        """Print the current game state: letters in top and bottom row"""
        top_row = self.get_top_row()
        bottom_row = self.get_bottom_row()

        print(" ".join(l.ljust(2) for l in top_row))
        print(" ".join(str(i).zfill(2) for i in range(1, self.n_letters + 1)))
        print(" ".join(l.ljust(2) for l in bottom_row))

    def buy_letter(self, top_row_position: int) -> Tuple[int, str]:
        """Buy the letter of a position in the top row

        Will then be shown in the bottom row in the correct place

        Parameters
        ----------
        top_row_position : int
            The position of the letter to be bought

        Returns
        -------
            bottom_row_position : int
                THe position where the letter will land
            bottom_row_str : str
                The single character (true letter or "?" if incorrect) to be shown in the bottom row
        """
        if top_row_position not in range(1, self.n_letters + 1):
            raise ValueError(
                f"top_row_position must be an int from 1 to {self.n_letters}"
            )

        top_row_state = self.state[top_row_position]
        if top_row_state["bought"]:
            raise ValueError(f"{top_row_position} already bought!")

        top_row_state["bought"] = True
        if top_row_state["correct"]:
            return top_row_state["answer_position"], top_row_state["true_letter"]
        return top_row_state["answer_position"], "?"

    def make_guess(self, guess):
        """Handle the guess as made by the user"""
        self.guesstime = datetime.datetime.now()
        self.guess = guess.lower().replace("ij", "\u0133")
        if self.guess == self.answer:
            print(f"You won! The answer was {self.answer!r}")
        else:
            print(f"You lost! The answer was {self.answer!r}, not {guess!r}")

    def _write_to_file(self):
        output_path = os.path.join("Output", f"{self.__class__.__name__}.csv")
        file_exists = os.path.isfile(output_path)

        results = {
            "Answer": self.answer,
            "Guess": self.guess,
            "start_time": self.start_time,
            "Guesstime": self.guesstime,
        }
        by_quizposition = dict(sorted(self.state.items()))
        for quizposition, state in by_quizposition.items():
            for key, value in state.items():
                results[f"{quizposition}_{key}"] = value
        with open(output_path, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, results.keys())
            if not file_exists:
                w.writeheader()
            w.writerow(results)

    def play(self, write=True):
        """Play one round of the Woordrader game as text"""
        self.start_time = datetime.datetime.now()
        while self.guess is None:
            self.show_guess_panel()
            inp = input("Enter guess or placement of letter to buy")
            try:
                inp = int(inp)
            except ValueError:
                pass

            if isinstance(inp, int):
                self.buy_letter(inp)
            else:
                self.make_guess(inp)
        if write:
            self._write_to_file()
