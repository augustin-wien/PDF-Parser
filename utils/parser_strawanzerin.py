"""Parsing functions to extract images and text from strawanzerin PDF file."""

# import traceback

import os

import fitz
from utils.parser_augustin import parse_image

# from utils import requests


class Strawanzerin:
    """Class for common utility functions for the plugin."""

    def __init__(self):
        self.debug = os.environ.get("DEBUG")
        self.global_url = os.environ.get("SAVE_PATH")

    def parse_strawanzerin_image(self, save_path_for_pdf, path_to_new_directory):
        """Parse the strawanzerin file."""

        # Get source file
        src = fitz.open(save_path_for_pdf)

        # Get image from first page
        page = src.load_page(0)

        index = "strawanzerin"

        # Get image from PDF
        number_of_images, image_id, _ = parse_image(
            page, src, index, path_to_new_directory
        )

        if number_of_images != 1:
            print("Error: Number of images found is not 1!")

        return image_id

    def parse_strawanzerin_headline(self, src, only_first_page=False):
        """Parse the strawanzerin file for headlines."""

        for index, page in enumerate(src):
            headlines = []
            # Skip first page if only_first_page is True
            if index == 0 and not only_first_page:
                continue

            blocks = page.get_text("dict", flags=11)["blocks"]
            for block in blocks:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > 30:
                            headlines += span["text"], span["bbox"], span["size"]

            # Return headlines after one for loop if only_first_page is True
            if only_first_page:
                return headlines

        return headlines

    def parse_strawanzerin_first_page(self, save_path_for_pdf, path_to_new_directory):
        """Parse the strawanzerin file."""

        # Get source file
        src = fitz.open(save_path_for_pdf)

        page = src.load_page(0)

        headline = self.parse_strawanzerin_headline(src, True)

        if not headline:
            print("Error: No headline found!")

        if headline[3].lower() == "gratis":
            x0, y0, x1, y1 = headline[4]
            print("gratis", x0, y0, x1, y1)
        else:
            raise ValueError("Error: No headline gratis found!")

        clip_regions = [
            (0, 0, page.rect.width, y0),
            (0, y0, 180, page.rect.height),
            (180, y0, 320, page.rect.height),
            (320, y0, 460, page.rect.height),
            (460, y0, page.rect.width, page.rect.height),
        ]
        text = ""
        for i, (x0, y0, x1, y1) in enumerate(clip_regions):
            clip_region = (x0, y0, x1, y1)
            text += page.get_text("text", clip=clip_region)

            # Save the image to the new directory
            if self.debug:
                name_png = f"{path_to_new_directory}page-{page.number}{i + 1}.png"
                pix = page.get_pixmap(clip=clip_region)
                pix.save(name_png)

        return text

    def parse_strawanzerin(self, save_path_for_pdf, path_to_new_directory):
        """Parse the strawanzerin file."""
        # parse_strawanzerin_image(save_path_for_pdf, path_to_new_directory)
        text = self.parse_strawanzerin_first_page(
            save_path_for_pdf, path_to_new_directory
        )
        print(text)
