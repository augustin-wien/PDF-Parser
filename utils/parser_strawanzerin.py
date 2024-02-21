"""Parsing functions to extract images and text from strawanzerin PDF file."""

import os

import fitz
from utils import requests
from utils.parser_augustin import parse_image


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
            raise ValueError("Error: Number of images found is not 1!")

        return image_id

    def parse_strawanzerin_headline(self, page):
        """Parse the strawanzerin file for headlines."""
        headlines = []
        blocks = page.get_text("dict", flags=11)["blocks"]
        for block in blocks:
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["size"] > 30:
                        headlines += span["text"], span["bbox"], span["size"]

        return headlines

    def flags_decomposer(self, flag):
        """Make font flags human readable."""
        flags = []
        if flag & 2**0:
            flags.append("superscript")
        if flag & 2**1:
            flags.append("italic")
        if flag & 2**2:
            flags.append("serifed")
        else:
            flags.append("sans")
        if flag & 2**3:
            flags.append("monospaced")
        else:
            flags.append("proportional")
        if flag & 2**4:
            flags.append("bold")
        return ", ".join(flags)

    def add_html_tags_to_text(self, page, clip_region):
        """Extract metadata from the PDF page."""
        text = ""
        blocks = page.get_text("dict", clip=clip_region, sort=True, flags=11)["blocks"]
        for block in blocks:
            for line in block["lines"]:
                for span in line["spans"]:
                    # Cover case for headlines with size > 30
                    if span["size"] > 30:
                        text += "<h2>" + span["text"] + "</h2>"
                        continue

                    # Cover case for headlines with different font color
                    if (
                        f'#{span["color"]:06x}' != "#221f1f"
                        or f'#{span["color"]:06x}' != "#000000"
                        and span["size"] > 20
                    ):
                        text += "<h3><b>" + span["text"] + "<b/></h3>"
                        continue

                    # Cover case for bold headlines with size > 10
                    if span["size"] > 10 and span["flags"] & 2**4:
                        text += "<h4><b>" + span["text"].upper() + "</b></h4>"
                        continue

                    # Cover case for italic fonts with size > 10
                    if span["size"] < 10 and span["flags"] & 2**1:
                        text += "<h5><i>" + span["text"] + "</i></h5>"
                        continue

                    # Cover case for bold headlines with size > 10
                    if span["size"] < 10 and span["flags"] & 2**4:
                        text += "<h5><b>" + span["text"] + "</b></h5>"
                        continue

                    text += span["text"]
        return text

    def parse_first_page(self, save_path_for_pdf, path_to_new_directory):
        """Parse the strawanzerin file."""

        # Get source file
        src = fitz.open(save_path_for_pdf)

        page = src.load_page(0)

        headlines = self.parse_strawanzerin_headline(page)

        if not headlines:
            raise ValueError("Error: No headline found!")

        if headlines[3].lower() == "gratis":
            x0, y0, x1, y1 = headlines[4]
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
            text += self.add_html_tags_to_text(page, clip_region)

            # Save the image to the new directory
            if self.debug:
                name_png = f"{path_to_new_directory}page-{page.number}{i + 1}.png"
                pix = page.get_pixmap(clip=clip_region)
                pix.save(name_png)

        return text

    def get_clip_regions(self, page, headlines, even_page_number):
        """Get clip regions for specified page."""
        if len(headlines) == 0:
            if even_page_number:
                clip_regions = [
                    (0, 0, 180, page.rect.height),
                    (180, 0, 320, page.rect.height),
                    (320, 0, 460, page.rect.height),
                    (460, 0, page.rect.width, page.rect.height),
                ]
            else:
                clip_regions = [
                    (0, 0, 160, page.rect.height),
                    (160, 0, 300, page.rect.height),
                    (300, 0, 440, page.rect.height),
                    (440, 0, page.rect.width, page.rect.height),
                ]
        elif len(headlines) == 3:
            if even_page_number:
                clip_regions = [
                    (0, 0, 180, headlines[1][1]),
                    (180, 0, 320, headlines[1][1]),
                    (320, 0, 460, headlines[1][1]),
                    (0, headlines[1][1], 180, page.rect.height),
                    (180, headlines[1][1], 320, page.rect.height),
                    (320, headlines[1][1], 460, page.rect.height),
                    (460, 0, page.rect.width, page.rect.height),
                ]
            else:
                clip_regions = [
                    (0, 0, 160, headlines[1][1]),
                    (160, 0, 300, headlines[1][1]),
                    (300, 0, 440, headlines[1][1]),
                    (0, headlines[1][1], 160, page.rect.height),
                    (160, headlines[1][1], 300, page.rect.height),
                    (300, headlines[1][1], 440, page.rect.height),
                    (440, 0, page.rect.width, page.rect.height),
                ]
        elif len(headlines) == 6:
            if even_page_number:
                clip_regions = [
                    (0, 0, 180, headlines[1][1]),
                    (180, 0, 320, headlines[1][1]),
                    (320, 0, 460, headlines[1][1]),
                    (0, headlines[1][1], 180, headlines[4][1]),
                    (180, headlines[1][1], 320, headlines[4][1]),
                    (320, headlines[1][1], 460, headlines[4][1]),
                    (0, headlines[4][1], 180, page.rect.height),
                    (180, headlines[4][1], 320, page.rect.height),
                    (320, headlines[4][1], 460, page.rect.height),
                    (460, 0, page.rect.width, page.rect.height),
                ]
            else:
                clip_regions = [
                    (0, 0, 160, headlines[1][1]),
                    (160, 0, 300, headlines[1][1]),
                    (300, 0, 440, headlines[1][1]),
                    (0, headlines[1][1], 160, headlines[3][1]),
                    (160, headlines[1][1], 300, headlines[3][1]),
                    (300, headlines[1][1], 440, headlines[3][1]),
                    (0, headlines[3][1], 160, page.rect.height),
                    (160, headlines[3][1], 300, page.rect.height),
                    (300, headlines[3][1], 440, page.rect.height),
                    (440, 0, page.rect.width, page.rect.height),
                ]
        else:
            raise ValueError("Error: Number of headlines found is not 0, 3 or 6!")

        return clip_regions

    def get_text_from_pages(self, page, headlines, even_page_number):
        """Parse the strawanzerin file."""
        text, column_text = "", ""
        if even_page_number:
            clip_regions = self.get_clip_regions(page, headlines, True)
        else:
            clip_regions = self.get_clip_regions(page, headlines, False)

        for index, (x0, y0, x1, y1) in enumerate(clip_regions):
            clip_region = (x0, y0, x1, y1)

            # Only add the last column to the variable column_text
            if index == len(clip_regions) - 1:
                column_text += self.add_html_tags_to_text(page, clip_region)
                continue

            text += self.add_html_tags_to_text(page, clip_region)

        return text, column_text

    def parse_following_pages(self, save_path_for_pdf):
        """Parse page two of the strawanzerin file."""
        # Get source file
        src = fitz.open(save_path_for_pdf)

        text, column_text = "", ""

        for index, page in enumerate(src):
            if index == 0:
                continue

            headlines = self.parse_strawanzerin_headline(page)

            # Since index starts at zero, even index number means odd page number
            even_index_number = index % 2 == 1
            text_array = self.get_text_from_pages(page, headlines, even_index_number)
            text += text_array[0]
            column_text += text_array[1]

        # Finally merge the last column to the text
        text += column_text

        return text

    def parse_strawanzerin(self, save_path_for_pdf, path_to_new_directory):
        """Parse the strawanzerin file."""
        image_id = self.parse_strawanzerin_image(
            save_path_for_pdf, path_to_new_directory
        )
        text = self.parse_first_page(save_path_for_pdf, path_to_new_directory)
        text += self.parse_following_pages(save_path_for_pdf)

        # Post raw text and category to Wordpress backend with exception handling in function
        requests.upload_post("strawanzerin", "Strawanzerin", text, image_id)
