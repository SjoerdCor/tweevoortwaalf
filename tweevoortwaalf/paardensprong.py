""" Generate Paardensprong puzzle and show it"""

from typing import List

import pandas as pd

from .woordpuzzel import PuzzleImage, Woordpuzzel


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

    def _unique_solution(self):
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
        generator = PaardensprongImageGenerator(puzzle)
        generator.generate_image()
        generator.show_image()


# pylint: disable=too-many-instance-attributes
class PaardensprongImageGenerator(PuzzleImage):
    """Generates an image of a 3x3 letter puzzle with a central text."""

    def __init__(self, puzzle):
        """
        Initialize the image generator.

        puzzle must be a 3 x 3 grid of placed letters
        """
        super().__init__()
        self.grid_size = 3
        self.cell_size = self.width // self.grid_size
        self.circle_radius = self.cell_size // 3
        self.letters = puzzle
        self.font = self.load_font()

    def draw_grid(self):
        """Draw the grid lines for the puzzle."""
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if (row, col) != (1, 1):  # Do not draw black letters on the center

                    # draw white background
                    x0 = (col + 0.1) * self.cell_size
                    y0 = (row + 0.1) * self.cell_size
                    x1 = x0 + self.cell_size * 0.8
                    y1 = y0 + self.cell_size * 0.8
                    self.draw.rectangle([x0, y0, x1, y1], fill="white", outline="white")

                    # draw letter
                    text = self.letters[row][col]
                    bbox = self.draw.textbbox((0, 0), text, font=self.font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = x0 + (self.cell_size * 0.8 - text_width) // 2
                    y = y0 + (self.cell_size * 0.8 - text_height) // 2
                    self.draw.text((x, y), text.upper(), fill="black", font=self.font)

    def draw_center_text(self):
        """Draw the central text '2V12'."""
        center_x = self.width // 2
        center_y = self.height // 2
        self.draw.arc(
            (
                center_x - self.circle_radius,
                center_y - self.circle_radius,
                center_x + self.circle_radius,
                center_y + self.circle_radius,
            ),
            start=300,
            end=270,
            fill="white",
            width=5,
        )

        # Adjust font size for central text
        central_text = "2V\n12"
        font = self.load_font(40)
        bbox = self.draw.textbbox((0, 0), central_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        self.draw.text(
            (center_x - text_width // 2, center_y - text_height // 2),
            central_text,
            fill="white",
            font=font,
            align="center",
        )

    def generate_image(self):
        """Generate the complete image."""
        self.draw_grid()
        self.draw_center_text()
