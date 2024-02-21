"""Parsing functions to extract images and text from PDF."""

import traceback
import fitz

from utils import requests


# Method to extract all images from a PDF page
def get_all_images(page, index, src, path_to_new_directory):
    """Get all images from a PDF page."""
    # Get image from PDF
    img_list = page.get_images(full=True)

    highest_index = 0

    for img_index, image in enumerate(img_list):
        image_index = image[0]
        base_image = src.extract_image(image_index)
        image_bytes = base_image["image"]

        # Save the image to a file
        image_filename = f"{path_to_new_directory}page_{index}_img_{img_index}.png"
        with open(image_filename, "wb") as image_file:
            image_file.write(image_bytes)

        highest_index = img_index

    return highest_index


# Function creates meta information for the post
def create_meta_information(category, headline=None):
    """Create meta information for the post."""
    # If headline is not given, use category as title
    headline_or_category = headline if headline else category
    meta_information = {
        "protocol": "",
        "photograph": "",
        "title": headline_or_category,
        "author": "",
        "category": category,
    }
    return meta_information


def clean_text(raw_text, starting_characters):
    """Clean the text from unwanted newlines and hyphens."""
    found_starting_character = False

    article = ""

    for line in raw_text.split("\n"):
        if found_starting_character:
            # Skip empty lines
            if not line.strip():
                continue

            # Clean text from unwanted hyphens and add newlines, if line is not empty
            try:
                if line.endswith(" "):
                    if line[-2] in [".", "!", "?", ":"]:
                        article += line[:-1] + "\n"
                        continue
                    article += line
                    continue
                # If in the end of line is "." or "!" or "?" or ":" keep newline
                if line.endswith((".", "!", "?", ":")):
                    article += line + "\n"
                    continue
                # If in the end of line is "-" delete hyphen and add line to article
                if line[-1] == "-":
                    article += line[:-1]
                    continue
            except IndexError:
                pass

            # If no checks are met, add line to article
            article += line

        if starting_characters[0] == line:
            found_starting_character = True
            article += line

    # Format the string
    article = list(article)
    article_edit = article
    for index, letter in enumerate(article):
        if letter == "■":
            del article_edit[index:]
        if " " in letter and " " in article[index - 1]:
            del article_edit[index]

    return "".join(article_edit)


def extract_starting_characters(
    span, starting_characters=None, searching_for_end=False
):
    """Extract starting characters."""
    if (
        not span["text"].isdigit()
        and len(span["text"]) < 3
        and span["text"] != "■"
        and not searching_for_end
    ):
        if starting_characters is None:
            starting_characters = []
        starting_characters.append(span["text"].strip())
    return starting_characters


def extract_ending_symbols(span, ending_symbols):
    """Extract ending symbols."""
    if "■" in span["text"]:
        ending_symbols += 1
    return ending_symbols


def process_span(
    span, starting_characters, ending_symbols, headlines, searching_for_end
):
    """Process a span."""
    font_size = span["size"]
    colour_code = f"#{span['color']:06x}"

    # Check if colour code is not black or dark brown since starting characters have version colour
    if colour_code not in ("#2e2013", "#000000"):
        starting_characters = extract_starting_characters(
            span, starting_characters, searching_for_end
        )
        ending_symbols = extract_ending_symbols(span, ending_symbols)

    # ------ Header check ------
    # Check if font is bold and font size is larger 12
    if font_size > 12 or span["font"] == "AmasisMTStd-Bold":
        if headlines is None:
            headlines = []
        if not searching_for_end:
            headlines.append(span["text"].strip())

    return starting_characters, ending_symbols, headlines


def extract_headlines(
    page, starting_characters=None, headlines=None, searching_for_end=False
):
    """Extract headlines from a PDF page."""
    ending_symbols = 0
    text_instances = page.get_text("dict", sort=True)["blocks"]

    if not text_instances:
        return headlines, starting_characters, ending_symbols

    for text in text_instances:
        try:
            for line in text["lines"]:
                for span in line["spans"]:
                    starting_characters, ending_symbols, headlines = process_span(
                        span,
                        starting_characters,
                        ending_symbols,
                        headlines,
                        searching_for_end,
                    )

        except KeyError:
            pass

    return headlines, starting_characters, ending_symbols


# Function returns all the text from the given PDF page
def extract_text(
    page,
    previous_raw_text=None,
    starting_characters=None,
    headlines=None,
    searching_for_end=False,
):
    """Get the raw text from the PDF page."""
    # get raw text from page
    raw_text = page.get_text()
    new_raw_text = (
        raw_text if previous_raw_text is None else previous_raw_text + " " + raw_text
    )

    # 1. Step: Check for headline and starting characters
    headlines, starting_characters, ending_symbols = extract_headlines(
        page, starting_characters, headlines, searching_for_end
    )

    article = ""
    if headlines and starting_characters:

        # 2. Step Check if article starts on page but no ending symbol is found i.e. ends on next page
        if (
            len(headlines) >= 1
            and len(starting_characters) >= 1
            and ending_symbols == 0
        ):
            return (
                (raw_text if previous_raw_text is None else new_raw_text),
                article,
                headlines,
                starting_characters,
            )

        # If ending symbol is found, clean raw text to readable article
        article = clean_text(
            raw_text if previous_raw_text is None else new_raw_text,
            starting_characters,
        )

    return (
        (raw_text if previous_raw_text is None else new_raw_text),
        article,
        headlines,
        starting_characters,
    )


def parse_image(page, src, index, path_to_new_directory):
    """
    Parse the images from a PDF page and upload them to the Wordpress backend.
    Returns number of images found, image_id of the first image and
    image_text where each image is embedded in case of more than one image.
    """
    try:
        number_of_images = get_all_images(page, index, src, path_to_new_directory)

        image_text = ""
        if number_of_images == 0:
            return number_of_images, 0, image_text
        # Exclude images that are not in the page rectangle
        rx = page.rect
        image_index= 0
        image_id = None
        image_src = None
        for img_info in page.get_images(full=True):
            img_rect = fitz.Rect(img_info[:4])
            if rx.contains(img_rect):
                image_filename = (
                    f"{path_to_new_directory}page_{index}_img_{image_index}.png"
                )
                image_id, image_src = requests.upload_image(
                    image_filename, f"page_{index}_img_{image_index}.png"
                )
                if number_of_images == 1:
                    return number_of_images, image_id, image_text
                # this shouldn't contain new lines because they are transforemd to <p> tags which are not block elements
                image_text += '<!-- wp:image {"id":'+str(image_id)+'} --><figure class="wp-block-image size-full"><img src="'+image_src+'"alt="" class="wp-image-'+str(image_id)+'"/></figure><!-- /wp:image -->'
            image_index += 1
    except IOError as e:
        traceback.print_exc()
        error_message = f"Error extracting and uploading images: {e}"
        raise IOError(error_message) from e

    return number_of_images, image_id, image_text


def parse_page(page, meta_array):
    """Parse a single page of a PDF file and upload it to the Wordpress backend."""

    # Extract raw text from page with exception handling
    try:
        if meta_array["raw_text"]:
            print("Extracting raw text with meta_array")
            raw_text, article, headlines, starting_characters = extract_text(
                page,
                meta_array["raw_text"],
                meta_array["starting_characters"],
                meta_array["headlines"],
                True,
            )
        else:
            raw_text, article, headlines, starting_characters = extract_text(page)
    except IOError as e:
        traceback.print_exc()
        error_message = f"Error extracting raw text: {e}"
        raise IOError(error_message) from e

    # Extract text of several pages if story starts on one page and ends on another
    # Set limit to maximum 10 pages if no ending symbol can be found
    if not article and headlines and starting_characters:
        return raw_text, headlines, starting_characters, True

    # Since all headlines are given, join all headlines to one string
    if headlines is None:
        headlines = []
    headline = " ".join(headlines)

    # Try posting raw text and category to Wordpress backend with exception handling
    try:
        meta_information = create_meta_information(meta_array["category"], headline)

        # If article is not empty, set raw_text to article
        if article:
            raw_text = article

        # Append image_text to raw_text
        raw_text += meta_array["image_text"]

        # Post to Wordpress
        response = requests.upload_post(
            meta_information, raw_text, meta_array["image_id"]
        )
    except IOError as e:
        traceback.print_exc()
        error_message = (
            f"WPLocal not running? No connection established uploading from main: {e}"
        )
        raise IOError(error_message) from e

    if response.status_code not in [200, 201]:
        raise IOError(
            f"Error posting to Wordpress: {response.content} with status code {response.status_code}"
        )

    return raw_text, headlines, starting_characters, False
