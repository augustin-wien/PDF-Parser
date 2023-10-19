"""Extracts the text from the cover page of the PDF file."""
# Import necessary libraries

import re

import fitz
from utils import upload_image


def save_page_0_as_image(path_to_file):
    """Save the cover page of the PDF file as a PNG image."""
    src = fitz.open(path_to_file)

    page = src.load_page(0)
    pix = page.get_pixmap()  # render page to an image
    # TODO extract the number in a more dynamical way!!
    # This will lead to an error if the directory name changes
    number_in_dir = [int(s) for s in re.findall(r"\d+", path_to_file)]
    #number_in_dir = [number_in_dir]
    if len(number_in_dir) != 1:
        raise ValueError(
            "No number found in directory name", number_in_dir, path_to_file
        )
    image_title = "coverpage-version-%i" % (number_in_dir[0])
    image_path = "sample_data/" + image_title + ".png"
    pix.save(
        image_path,
    )

    image_id = upload_image(image_path, image_title)

    return image_id


# WARNING: Here the code relies on the words "Registrierte " and "tragen"
def extract_color_code(path_to_file):
    """Extract the color code from the cover page of the PDF file."""
    src = fitz.open(path_to_file)
    page = src[0]

    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = page.get_text("dict", flags=11)["blocks"]
    for block in blocks:  # iterate through the text blocks
        for line in block["lines"]:  # iterate through the text lines
            for span in line["spans"]:  # iterate through the text spans
                if span["text"] == "Registrierte ":
                    color_code = span["color"]
                if span["text"] == "tragen" and color_code == span["color"]:
                    hex_color_code = "#%06x" % color_code

    return hex_color_code
