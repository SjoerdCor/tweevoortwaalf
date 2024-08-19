"""Base class for paardensprong and taartpuzzel"""

import abc
import csv
import os
import random
import time

import pandas as pd


class NonUniqueQuizException(Exception):
    """Raised when a puzzle has multiple solutions"""


class Woordpuzzel:
    """Base class for paardensprong and taartpuzzel"""

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

    @property
    @abc.abstractmethod
    def n_letters(self) -> int:
        """The number of letters in the puzzle"""

    @abc.abstractmethod
    def unique_solution(self):
        """Determines whether puzzle has a unique solutions. Must be implemented by subclasses"""

    @abc.abstractmethod
    def create_puzzle(self):
        """Creates the puzzle. Must be implemented by subclasses"""

    @abc.abstractmethod
    def show_puzzle(self, puzzle):
        """Shows the puzzle as image. Must be implemented by subclasses"""

    def select_puzzle(self):
        """Selects the puzzle answer"""
        wordlist = pd.read_csv(
            f"tweevoortwaalf/Data/suitable_{self.n_letters}_letter_words.txt",
            header=None,
        ).squeeze()
        self.answer = wordlist.sample(1).squeeze()

    def _write_to_file(self):
        output_path = os.path.join("Output", f"{self.__class__.__name__}.csv")

        file_exists = os.path.isfile(output_path)

        with open(output_path, "a", encoding="utf-8") as f:
            w = csv.DictWriter(f, self.__dict__.keys())
            if not file_exists:
                w.writeheader()
            w.writerow(self.__dict__)

    @staticmethod
    def clean_guess(guess):
        """Make strings comparable"""
        return guess.lower().replace("ij", "\u0133")

    def play(self, write=True):
        """Play the game interactively"""
        if not self.unique_solution():
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
