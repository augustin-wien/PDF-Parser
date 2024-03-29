"""Extracts the text from the first page of the PDF file."""

import os
import sys

import fitz
from dotenv import load_dotenv
from utils.requests import upload_post
from utils.utils import PluginUtility

sys.path.append("../")

load_dotenv()

global_url = os.environ.get("WORDPRESS_URL")

plugin_utility = PluginUtility()


def create_post(page, image_id, category, category_papers_id):
    """Create a post with the extracted text and the uploaded image."""

    # Get the text from the page
    r2, article = calculate_extraction_rectangles(page)

    meta_information = {
        "protocol": "",
        "photograph": "",
        "title": "",
        "author": "",
        "category": category,
    }

    meta_array = page.get_textbox(r2).splitlines()

    # WARNING: This is not dynamic and only relies on the word "protokoll"
    # Assign meta data to variables
    meta_dict = {"title": "", "author": "", "photograph": "", "protocol": ""}
    for i, line in enumerate(meta_array):
        if "protokoll:" in line.lower():
            meta_dict["protocol"] = meta_array[i].lower().title()
            meta_dict["photograph"] = meta_array[i + 1].lower().title()
            meta_dict["author"] = "Autor*in: " + meta_array[i - 2].lower().title()
            meta_dict["title"] = meta_array[i - 1]

    for key, value in meta_dict.items():
        if value.strip() == "":
            meta_dict[key] = "Kein " + key

    # Format the string
    article = list(article)
    article_edit = article
    for index, letter in enumerate(article):
        # deletes newlines that are made up because of articles structure
        if "\n" in letter:
            if (
                "." in article[index - 1]
                or "!" in article[index - 1]
                or "?" in article[index - 1]
                or ":" in article[index - 1]
            ):
                print("supposed to break a new line", letter)

            elif "-" in article[index - 1]:
                if " " in article[index - 1] and " " in article[index + 1]:
                    # this hyphen has been set on purpose and stays
                    print("hyphen has been set on purpose")
                else:
                    # deletes hyphen on the index and the extra space before it
                    del article_edit[index]
                    del article_edit[index - 1]
            else:
                del article_edit[index]
        # deletes double spaces
        if " " in letter and " " in article[index - 1]:
            del article_edit[index]

    # to create a readable text for the article
    readable_text = "".join(article_edit)
    meta_information["category_paper"] = category_papers_id

    response = upload_post(meta_information, readable_text, image_id)

    print("response", response.content)

    return response.content


def calculate_extraction_rectangles(page):
    """Calculate the height of the extraction rectangles."""
    # First, create rect for article text which is on the bottom third of page
    r = page.rect
    r.y0 = (r.y1 * 2) / 3  # two third of page height
    article = page.get_textbox(r)

    # Second, create rect for article title
    # which is in between half and third bottom of page
    r2 = page.rect
    r2.y0 = r2.y1 / 2  # half of page height
    r2.y1 = r2.y1 * 2 / 3 - 3  # two third of page height -3 so no overlap
    return r2, article


def extract_page(pdf_file, category, category_papers_id):
    """Extract the text from the third page of the PDF file."""
    src = fitz.open(pdf_file)
    new_doc = fitz.open()  # empty output PDF
    r2, page = calculate_rectangles_for(src)

    new_page = new_doc.new_page(-1, width=r2.width, height=r2.height)
    new_page.show_pdf_page(
        new_page.rect,
        src,
        page.number,
        clip=r2,
    )

    image_id = plugin_utility.download_image(new_page, new_doc, src)

    response = create_post(new_page, image_id, category, category_papers_id)

    return response


def calculate_rectangles_for(src):
    """Calculate the height of the page."""

    page = src.load_page(1)
    r = page.rect
    d = fitz.Rect(
        # CropBox displacement if being set
        page.cropbox_position,
        page.cropbox_position,
    )  # starting at (0, 0)

    r1 = r
    r1.x1 = r1.x1 / 2  # left side of double page
    r2 = r1 + (r1.width, 0, r1.width, 0)  # right side of double page
    # r2 = r + (r.width / 2, 0, 0, 0)  # right side of double page

    r2 += d  # add the CropBox displacement

    return r2, page
