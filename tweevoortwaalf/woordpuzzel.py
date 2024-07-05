import random
import time
import os
import csv

import pandas as pd


class NonUniqueQuizException(Exception):
    pass


class Woordpuzzel:
    def __init__(self, answer=None, direction=None, startpoint=None):
        if answer is None:
            self.select_puzzle()
        else:
            self.answer = answer
        # TODO: validate correctness of direction and startpoint
        self.direction = direction or random.choice([-1, 1])
        self.startpoint = startpoint or random.choice(range(self.n_letters))
        self.starttime = None
        self.guesstime = None
        self.guess = None
        self.correct = None

    def select_puzzle(self):
        suitability_cols = ['AllLowercase', 'AllBasicAlpha', 'ZelfstandigNaamwoord', 'IsEnkelvoud']

        df = pd.read_csv('Data/wordlist.csv').assign(Suitable = lambda df: df[suitability_cols].fillna(False).all('columns'))

        self.answer = (df
            .query("Suitable & Length == @self.n_letters")["Word"]
            .sample(1)
            .squeeze()
        )

    def _write_to_file(self):
        output_path = os.path.join("Output", f"{self.__class__.__name__}.csv")

        file_exists = os.path.isfile(output_path)

        with open(output_path, "a", encoding="utf-8") as f:
            w = csv.DictWriter(f, self.__dict__.keys())
            if not file_exists:
                w.writeheader()
            w.writerow(self.__dict__)


    def clean_guess(self, guess):
        return guess.lower().replace("ij", "\u0133")

    def play(self, write=True):
        if not self._unique_solution():
            raise NonUniqueQuizException(f"More than one solution for {self.answer!r}")

        puzzle = self.create_puzzle()
        self.show_puzzle(puzzle)
        self.starttime = time.time()
        self.guess = input("")
        self.guesstime = time.time() - self.starttime
        self.correct = self.clean_guess(self.guess) == "".join(self.answer)
        if self.correct:
            print(f"You won! The answer was {self.answer!r}")
        else:
            print(f"You lost! The answer is {self.answer!r}")
        if write:
            self._write_to_file()
