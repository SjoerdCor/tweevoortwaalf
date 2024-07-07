import random
import time
import os
import csv

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
    n_letters = 12

    def __init__(self, answer=None):
        if answer is None:
            answer = self.select_puzzle()
        else:
            self.answer = answer

        self.state = self._generate_starting_position()

        self.guess = None
        self.bought_letters = []
        self.starttime = None
        self.guesstime = None

    def select_puzzle(self):
        suitability_cols = ['AllLowercase', 'AllBasicAlpha', 'ZelfstandigNaamwoord', 'IsEnkelvoud']

        df = pd.read_csv('Data/wordlist.csv').assign(Suitable = lambda df: df[suitability_cols].fillna(False).all('columns'))

        self.answer = (df
            .query("Suitable & Length == @self.n_letters")["Word"]
            .sample(1)
            .squeeze()
        )


    def _generate_starting_position(self, p_wrong=0.05, p_unknown=0.05):
        # TODO: validate correct p's

        state = {}

        quizpositions = random.sample(range(self.n_letters), self.n_letters)
        for answer_position, (letter, quizposition) in enumerate(
            zip(self.answer, quizpositions)
        ):
            # TODO: allow for missing answers
            random_nr = random.random()
            if random_nr < p_wrong:
                shown_letter = random.choices(
                    list(LETTER_OCCURENCE_FIRST_POSITION.keys()),
                    list(LETTER_OCCURENCE_FIRST_POSITION.values()),
                )[0]
                correct = False
            elif p_wrong < random_nr < p_wrong + p_unknown:
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
        return state

    def _calculate_known_letters(self):
        by_answeringposition = dict(
            sorted(self.state.items(), key=lambda item: item[1]["answer_position"])
        )

        knownletters = []
        for quizplacement, state in by_answeringposition.items():
            if state["bought"]:
                if state["correct"]:
                    knownletters.append(state["true_letter"])
                else:
                    knownletters.append("?")
            else:
                knownletters.append("")
        return knownletters

    def show_guess_panel(self):

        by_quizposition = dict(sorted(self.state.items()))
        print(
            " ".join(
                state["shown_letter"].ljust(2) if not state["bought"] else "  "
                for quizplacement, state in by_quizposition.items()
            )
        )

        print(" ".join(str(i).zfill(2) for i in range(1, self.n_letters + 1)))

        knownletters = self._calculate_known_letters()
        print(" ".join(l.ljust(2) for l in knownletters))

    def buy_letter(self, i):
        if i not in range(1, self.n_letters + 1):
            return ValueError(f"i must be an int from 1 to {self.n_letters}")
        if self.state[i]["bought"]:
            return ValueError(f"{i} already bought!")

        # TODO: Add Joostens comment "The {letter} from {number} goes to {answer_number}"
        self.bought_letters.append(
            (self.state[i]["shown_letter"], self.state[i]["correct"])
        )
        self.state[i]["bought"] = True

    def make_guess(self, guess):
        self.guesstime = time.time() - self.starttime
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
            "Starttime": self.starttime,
            "Guesstime": self.guesstime,
            "BoughtLetters": self.bought_letters,
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
        self.starttime = time.time()
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
