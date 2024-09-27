"""Base class for paardensprong and taartpuzzel"""

import abc
import csv
import datetime
import importlib
import os
import random

import pandas as pd


class NonUniqueQuizException(Exception):
    """Raised when a puzzle has multiple solutions"""


class Woordpuzzel:
    """Base class for paardensprong and taartpuzzel"""

    def __init__(self, answer=None, direction=None, startpoint=None):
        self.start_time = None
        if answer is None:
            self.select_puzzle()
        else:
            self.answer = answer
        if direction not in [-1, 1, None]:
            raise ValueError(f"direction must be either -1 or 1, not {direction}")
        self.direction = direction or random.choice([-1, 1])
        if startpoint not in range(self.n_letters) and startpoint is not None:
            raise ValueError(
                f"startpoint must be in range({self.n_letters}) not {startpoint}"
            )
        if startpoint is not None:
            self.startpoint = startpoint
        else:
            self.startpoint = random.choice(range(self.n_letters))
        self.guesstime = None
        self.guess = None
        self.correct = None

    @property
    @abc.abstractmethod
    def n_letters(self) -> int:
        """The number of letters in the puzzle"""

    @property
    def wordlist(self) -> pd.Series:
        """Get all suitable words"""
        data_path = importlib.resources.files("tweevoortwaalf.Data").joinpath(
            f"suitable_{self.n_letters}_letter_words.txt"
        )
        return pd.read_csv(data_path).squeeze()

    @abc.abstractmethod
    def unique_solution(self):
        """Determines whether puzzle has a unique solutions. Must be implemented by subclasses"""

    @abc.abstractmethod
    def create_puzzle(self):
        """Creates the puzzle. Must be implemented by subclasses"""
        # TODO: set guess and guesstime to None

    @abc.abstractmethod
    def show_puzzle(self, puzzle):
        """Shows the puzzle as image. Must be implemented by subclasses"""

    def select_puzzle(self):
        """Selects the puzzle answer"""
        self.answer = self.wordlist.sample(1).squeeze()
        self.start_time = datetime.datetime.now()  # TODO: move to create_puzzle

    def _write_to_file(self):
        output_path = os.path.join("Output", f"{self.__class__.__name__}.csv")

        file_exists = os.path.isfile(output_path)

        with open(output_path, "a", encoding="utf-8") as f:
            w = csv.DictWriter(f, self.__dict__.keys())
            if not file_exists:
                w.writeheader()
            w.writerow(self.__dict__)

    @staticmethod
    def clean_string(guess):
        """Make strings comparable"""
        return guess.lower().strip().replace("ij", "\u0133")

    def check_guess(self, guess: str) -> None:
        """Check whether the guess is correct

        Cleans both guess and answer first
        """
        self.guess = guess
        self.correct = self.clean_string(self.guess) == self.clean_string(self.answer)
        self.guesstime = datetime.datetime.now()

    def play(self, write=True):
        """Play the game interactively"""
        if not self.unique_solution():
            raise NonUniqueQuizException(f"More than one solution for {self.answer!r}")

        puzzle = self.create_puzzle()
        self.show_puzzle(puzzle)
        guess = input("")
        self.check_guess(guess)

        if self.correct:
            print(f"You won! The answer was {self.answer!r}")
        else:
            print(f"You lost! The answer is {self.answer!r}")
        if write:
            self._write_to_file()
