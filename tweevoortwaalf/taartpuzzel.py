"""Generate the Taartpuzzle image and show it"""

import random

import pandas as pd

from .woordpuzzel import Woordpuzzel


class Taartpuzzel(Woordpuzzel):
    """Generate the Taartpuzzle image and show it"""

    n_letters = 9

    def __init__(self, missing_letter_index=None, **kwargs):
        super().__init__(**kwargs)
        self.missing_letter_index = missing_letter_index or random.choice(
            range(self.n_letters)
        )

    def unique_solution(self):
        """Rotations can not lead to an alternative solution"""
        otherwords = pd.read_csv(
            "tweevoortwaalf/Data/suitable_9_letter_words.txt", header=None
        ).squeeze()
        pattern = (
            self.answer[: self.missing_letter_index]
            + "."
            + self.answer[self.missing_letter_index + 1 :]
        )

        def rotate(strg, n):
            """Start at a different position

            Parameters
            ----------
            strg : str
                The string to be rotated
            n : int
                The number of places to rotate; must be less than or equal to length of wrd
            """
            return strg[n:] + strg[:n]

        n_options = []
        options = []
        for i in range(len(self.answer)):
            pat = rotate(pattern, i)
            matching = otherwords.str.match(pat)
            options.append(otherwords[matching])
            n_options.append(otherwords.str.match(pat).sum())
        return sum(n_options) == 1

    def create_puzzle(self):
        """Create the puzzle as list of letter with correct placement"""
        endpoint = self.startpoint + self.n_letters * self.direction
        placements = [
            self.answer[i % self.n_letters]
            for i in range(self.startpoint, endpoint, self.direction)
        ]
        placements[self.missing_letter_index] = "?"
        return placements

    def show_puzzle(self, puzzle):
        """Show the puzzle as a nice image"""
        try:
            # pylint: disable=import-outside-toplevel
            from .puzzleimages import TaartpuzzleImage

            # pylint: enable=import-outside-toplevel
        except ImportError as e:
            raise RuntimeError(
                "Can not import Taartpuzzel. Did you install "
                "tweevoortwaalf[interactivegame] optional dependencies "
                "to play this in a notebook?"
            ) from e
        generator = TaartpuzzleImage(puzzle)
        generator.generate_image()
        generator.show_image()
