"""Parsing functions to extract images and text from augustin PDF file."""

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
        try:
            print(
                f"Extracting image {img_index} from page {index} and img_index {img_index}"
            )
            pix = fitz.Pixmap(src, image_index)  # pixmap from the image xref
        except RuntimeError as e:
            traceback.print_exc()
            error_message = f"Error extracting image: {e}"
            raise IOError(error_message) from e
        if pix.colorspace is None:  # no colorspace, i.e. a mask
            print("Warning: Image is a mask")
            abs_width = abs(pix.width)
            abs_height = abs(pix.height)
            pix2 = fitz.Pixmap(fitz.csGRAY, (0, 0, abs_width, abs_height), 0)
            # create a black image
            pix2.set_rect(pix.irect, [0])
            # use the mask from pix to set the alpha channel of pix2
            pix3 = fitz.Pixmap(pix2, pix)
            pix = pix3  # use the new pixmap

        # Save the image to a file
        image_filename = f"{path_to_new_directory}page_{index}_img_{img_index}.png"
        pix.save(image_filename)

        highest_index = img_index

    return highest_index


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

        for image_index in range(number_of_images + 1):
            image_filename = (
                f"{path_to_new_directory}page_{index}_img_{image_index}.png"
            )
            image_id, image_src = requests.upload_image(
                image_filename, f"page_{index}_img_{image_index}.png"
            )
            if number_of_images == 1:
                return number_of_images, image_id, image_text

            image_text += f"""
                <!-- wp:image "id":{image_id},"sizeSlug":"full","linkDestination":"none" -->
                <figure class="wp-block-image size-full"><img src="{image_src}"
                alt="" class="wp-image-{image_id}"/></figure><!-- /wp:image -->"""

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

    meta_array["title"] = headline if headline else meta_array["category"]

    # If article is not empty, set raw_text to article
    if article:
        raw_text = article

    # Append image_text to raw_text
    raw_text += meta_array["image_text"]

    # Post to Wordpress
    requests.upload_post(
        meta_array,
        raw_text,
        meta_array["image_id"],
    )

    return raw_text, headlines, starting_characters, False


def process_augustin_file(save_path_for_pdf, path_to_new_directory, plugin_utility):
    """Process the Augustin file."""

    # split file in single pages
    plugin_utility.save_pdf_a3_to_pdf_a4(save_path_for_pdf, path_to_new_directory)

    src = fitz.open(save_path_for_pdf)

    categories = []
    meta_array = {
        "category": "",
        "image_id": None,
        "image_text": "",
        "raw_text": "",
        "headlines": [],
        "starting_characters": [],
    }

    for index, page in enumerate(src):

        # skip first page
        if index == 0:
            continue

        # Identify category of page
        try:
            category = plugin_utility.identify_category(
                page, index, path_to_new_directory
            )
            categories.append(category)
        except IOError as e:
            traceback.print_exc()
            error_message = f"Error identifying category: {e}"
            raise IOError(error_message) from e

        number_of_images, image_id, image_text = parse_image(
            page, src, index, path_to_new_directory
        )

        if number_of_images == 0:
            meta_array["image_id"] = None
            meta_array["image_text"] = ""

        src = fitz.open(save_path_for_pdf)

        meta_array["category"] = category
        meta_array["image_id"] = image_id
        meta_array["image_text"] = image_text
        print(f"Entering parse page once meta_array: {meta_array}")

        raw_text, headlines, starting_characters, next_page_needed = parse_page(
            page, meta_array
        )
        if next_page_needed:
            print("Next page needed")
            # This case occurs when the page has its end on the next pages
            meta_array["raw_text"] = " ".join(meta_array["raw_text"]) + raw_text
            meta_array["headlines"] += headlines
            meta_array["starting_characters"] += starting_characters

            continue

        # This is the case when the page has been uploaded
        meta_array = {
            "category": "",
            "image_id": None,
            "image_text": "",
            "index": 0,
            "raw_text": "",
            "headlines": [],
            "starting_characters": [],
        }
        src.close()
