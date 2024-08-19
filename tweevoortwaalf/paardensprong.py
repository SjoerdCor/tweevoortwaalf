""" Generate Paardensprong puzzle and show it"""

from typing import List

import pandas as pd

from .woordpuzzel import Woordpuzzel


class Paardensprong(Woordpuzzel):
    """Generate Paardensprong puzzle and show it"""

    clockwise_order = [(0, 0), (1, 2), (2, 0), (0, 1), (2, 2), (1, 0), (0, 2), (2, 1)]
    n_letters = 8

    def rotate(self, wrd: str, n: int):
        """Start at a different position

        Parameters
        ----------
        wrd : str
            The string to be rotated
        n : int
            The number of places to rotate; must be less than or equal to length of wrd
        """
        return wrd[n:] + wrd[:n]

    def unique_solution(self):
        """Rotations can not lead to an alternative solution"""
        otherwords = set(
            pd.read_csv(
                "tweevoortwaalf/Data/suitable_8_letter_words.txt", header=None
            ).squeeze()
        )
        for i in range(1, len(self.answer)):
            if self.rotate(self.answer, i) in otherwords:
                return False
        return True

    def create_puzzle(self) -> List[List[str]]:
        """Create as a 3 x 3 grid of strings, each letter in the correct place"""
        endpoint = self.startpoint + self.n_letters * self.direction
        placements = [
            self.clockwise_order[i % self.n_letters]
            for i in range(self.startpoint, endpoint, self.direction)
        ]
        dct = dict(zip(placements, self.answer))
        dct[(1, 1)] = ""
        puzzle = [
            [dct[(0, 0)], dct[(0, 1)], dct[(0, 2)]],
            [dct[(1, 0)], dct[(1, 1)], dct[(1, 2)]],
            [dct[(2, 0)], dct[(2, 1)], dct[(2, 2)]],
        ]
        return puzzle

    def show_puzzle(self, puzzle):
        """Show the puzzle as a nice image"""
        try:
            # pylint: disable=import-outside-toplevel
            from .puzzleimages import PaardensprongImageGenerator

            # pylint: enable=import-outside-toplevel
        except ImportError as e:
            raise RuntimeError(
                "Can not import PaardensprongImageGenerator. Did you install "
                "tweevoortwaalf[interactivegame] optional dependencies "
                "to play this in a notebook?"
            ) from e
        generator = PaardensprongImageGenerator(puzzle)
        generator.generate_image()
        generator.show_image()
