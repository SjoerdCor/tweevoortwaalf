"""Generate the Taartpuzzle image and show it"""

import random

import numpy as np
import pandas as pd

from .woordpuzzel import PuzzleImage, Woordpuzzel


class Taartpuzzel(Woordpuzzel):
    """Generate the Taartpuzzle image and show it"""

    n_letters = 9

    def __init__(self, missing_letter_index=None, **kwargs):
        super().__init__(**kwargs)
        self.missing_letter_index = missing_letter_index or random.choice(
            range(self.n_letters)
        )

    def _unique_solution(self):
        """Rotations can not lead to an alternative solution"""
        otherwords = pd.read_csv(
            "tweevoortwaalf/Data/suitable_9_letter_words.txt", header=None
        ).squeeze()
        pattern = (
            "^"
            + self.answer[: self.missing_letter_index]
            + "."
            + self.answer[self.missing_letter_index + 1 :]
            + "$"
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
        generator = TaartpuzzleImage(puzzle)
        generator.generate_image()
        generator.show_image()


# pylint: disable=too-many-instance-attributes
class TaartpuzzleImage(PuzzleImage):
    """Generate the Taartpuzzle image"""

    def __init__(self, letters):
        super().__init__()
        self.letters = letters
        self.circle_center = (self.width // 2, self.height // 2)
        self.circle_radius = self.width // 3
        self.inner_circle_radius = self.width // 10
        self.angles = np.linspace(0, 2 * np.pi, 9, endpoint=False)
        self.font = self.load_font()

    def draw_inner_circle(self):
        """Draw the inner circle as an image"""
        self.draw.ellipse(
            (
                self.circle_center[0] - self.circle_radius,
                self.circle_center[1] - self.circle_radius,
                self.circle_center[0] + self.circle_radius,
                self.circle_center[1] + self.circle_radius,
            ),
            outline="white",
            width=5,
        )

    def draw_outer_circle(self):
        """Draw outer circle in image"""
        self.draw.ellipse(
            (
                self.circle_center[0] - self.inner_circle_radius,
                self.circle_center[1] - self.inner_circle_radius,
                self.circle_center[0] + self.inner_circle_radius,
                self.circle_center[1] + self.inner_circle_radius,
            ),
            fill="red",
            outline="white",
            width=5,
        )

    def draw_lines(self):
        """Draw the boxes for the letters to appear in"""
        for angle in self.angles:
            x_outer = self.circle_center[0] + int(self.circle_radius * np.cos(angle))
            y_outer = self.circle_center[1] + int(self.circle_radius * np.sin(angle))
            x_inner = self.circle_center[0] + int(
                self.inner_circle_radius * np.cos(angle)
            )
            y_inner = self.circle_center[1] + int(
                self.inner_circle_radius * np.sin(angle)
            )
            self.draw.line((x_inner, y_inner, x_outer, y_outer), fill="white", width=5)

    def draw_center_text(self):
        """Draw the central text '2V12'."""
        central_text = "2V\n12"
        bbox = self.draw.textbbox((0, 0), central_text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        self.draw.text(
            (
                self.circle_center[0] - text_width // 2,
                self.circle_center[1] - text_height // 2,
            ),
            central_text,
            fill="white",
            font=self.font,
            align="center",
        )

    def draw_letters(self):
        """Draw the letters in their respective segments."""
        for i, letter in enumerate(self.letters):
            angle = self.angles[i] + np.pi / 9  # Adjust the rotation for centering
            x = self.circle_center[0] + int(
                (self.circle_radius + self.inner_circle_radius) / 2 * np.cos(angle)
            )
            y = self.circle_center[1] + int(
                (self.circle_radius + self.inner_circle_radius) / 2 * np.sin(angle)
            )
            bbox = self.draw.textbbox((0, 0), letter, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            if letter == "?":
                fill_color = "yellow"
            else:
                fill_color = "white"
            self.draw.text(
                (x - text_width // 2, y - text_height // 2),
                letter.upper(),
                fill=fill_color,
                font=self.font,
            )

    def generate_image(self):
        """Generate the complete image."""

        # Framework for the puzzle
        self.draw_inner_circle()
        self.draw_outer_circle()
        self.draw_lines()
        self.draw_center_text()

        # The puzzle itself
        self.draw_letters()
