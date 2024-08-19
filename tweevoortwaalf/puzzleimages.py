"""Module for all images to be shown in Python as puzzle"""

from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class PuzzleImage:
    """Base class for puzzle images"""

    width = 500
    height = 500

    def __init__(self):
        self.image = Image.new("RGB", (self.width, self.height), "red")
        self.draw = ImageDraw.Draw(self.image)

    def load_font(self, font_size=40):
        """
        Load the font to be used in the image.

        :param font_size: Size of the font.
        :return: Loaded font.
        """
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            return ImageFont.load_default()

    def show_image(self):
        """Display the generated image."""
        buffer = BytesIO()
        self.image.save(buffer, format="PNG")
        buffer.seek(0)
        plt.figure(figsize=(6, 6))
        plt.imshow(Image.open(buffer))
        plt.axis("off")  # Hide the axes
        plt.show()


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
