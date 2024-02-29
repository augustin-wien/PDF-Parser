"""Parsing functions to extract images and text from augustin PDF file."""

import os
import traceback

import fitz
from utils import requests
from utils.requests import check_for_papers_category, create_papers_category


# Method to extract all images from a PDF page
def get_all_images(page, index, src, path_to_new_directory):
    """Get all images from a PDF page."""
    # Get image from PDF
    img_list = page.get_images(full=True)

    highest_index = 0
    gustl_id = None

    for img_index, image in enumerate(img_list):
        image_index = image[0]
        contains_gustl = False

        pix = fitz.Pixmap(src, image_index)  # pixmap from the image xref
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
            # check dimensions for gustl
            if abs_width > 2000 and abs_height > 1000:
                contains_gustl = True

        # Save the image to jpg or png depending on colorspace
        if str(pix.colorspace).strip() == "Colorspace(CS_CMYK) - DeviceCMYK":
            image_filename = f"{path_to_new_directory}page_{index}_img_{img_index}.jpg"
        else:
            image_filename = f"{path_to_new_directory}page_{index}_img_{img_index}.png"
        print(f"Saving image to {image_filename}, pix.colorspace: {pix.colorspace}")
        pix.save(image_filename)

        highest_index = img_index
        if contains_gustl:
            print(f"Found Gustl on page {index} with image index {img_index}")
            gustl_id = img_index

    # Increment highest index by 1 to get the number of images
    return highest_index + 1, gustl_id


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
        "category_papers": 1,
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
                    # DTODO: variables should have the same order
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
        number_of_images, gustl_id = get_all_images(
            page, index, src, path_to_new_directory
        )
        print(f"Gustl id is {gustl_id}")

        gustl_wp_id = None

        image_text = ""
        if number_of_images == 0:
            return number_of_images, 0, image_text, gustl_wp_id
        # Exclude images that are not in the page rectangle
        rx = page.rect
        image_index = 0
        image_id = None
        image_src = None
        for img_info in page.get_images(full=True):
            img_rect = fitz.Rect(img_info[:4])
            if rx.contains(img_rect) or image_index == gustl_id:
                image_filename = (
                    f"{path_to_new_directory}page_{index}_img_{image_index}.png"
                )
                image_id, image_src = requests.upload_image(
                    image_filename, f"page_{index}_img_{image_index}.png"
                )
                if number_of_images == 1:
                    return number_of_images, image_id, image_text, gustl_wp_id
                print(
                    f"Adding image {image_index} to image_text and gustl id is {gustl_id}"
                )
                if image_index == gustl_id:
                    print(f"Setting gustl_wp_id to {image_id}")
                    gustl_wp_id = image_id
                    # Don't add gustl to image_text
                    continue
                # this shouldn't contain new lines because they are transforemd to <p> tags which are not block elements
                image_text += (
                    '<!-- wp:image {"id":'
                    + str(image_id)
                    + '} --><figure class="wp-block-image size-full"><img src="'
                    + image_src
                    + '"alt="" class="wp-image-'
                    + str(image_id)
                    + '"/></figure><!-- /wp:image -->'
                )
            image_index += 1
    except IOError as e:
        traceback.print_exc()
        error_message = f"Error extracting and uploading images: {e}"
        raise IOError(error_message) from e

    return number_of_images, image_id, image_text, gustl_wp_id


def parse_page(page, meta_array):
    """Parse a single page of a PDF file and upload it to the Wordpress backend."""

    # Extract raw text from page with exception handling
    print(f"Status of upload_data_now: {meta_array.get('upload_data_now')}")
    if not meta_array.get("upload_data_now"):
        try:
            if meta_array["raw_text"]:
                print("Entering extract_text with raw_text")
                raw_text, article, headlines, starting_characters = extract_text(
                    page,
                    meta_array["raw_text"],
                    meta_array["starting_characters"],
                    meta_array["headlines"],
                    True,
                )
            else:
                print("Entering extract_text without raw_text")
                raw_text, article, headlines, starting_characters = extract_text(page)
        except IOError as e:
            traceback.print_exc()
            error_message = f"Error extracting raw text: {e}"
            raise IOError(error_message) from e

        # Extract text of several pages if story starts on one page and ends on another
        # Set limit to maximum 10 pages if no ending symbol can be found
        if not article and headlines and starting_characters:
            return raw_text, headlines, starting_characters, True

        # Prevent error if headlines is None
        if headlines is None:
            headlines = []
        headline = " ".join(headlines)
    else:
        headline, article = "", ""
        headlines = meta_array["headlines"]
        starting_characters = meta_array["starting_characters"]
    # Try posting raw text and category to Wordpress backend with exception handling
    try:

        meta_information = create_meta_information(
            meta_array["category"],
            # Join headlines from variable or from meta_array depending on upload_data_now status
            (
                headline
                if not meta_array.get("upload_data_now")
                else " ".join(meta_array["headlines"])
            ),
        )
        meta_information["category_papers"] = meta_array["category_papers"]

        # If article is not empty, set raw_text to article
        if article and not meta_array.get("upload_data_now"):
            raw_text = article
        else:
            raw_text = meta_array["raw_text"]

        response = None
        # Append image_text to raw_text
        raw_text += meta_array["image_text"]
        if meta_array["category"] == "editorial":
            response = requests.upload_paper(
                meta_information, raw_text, meta_array["image_id"]
            )
        else:
            # Post Article to Wordpress
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


def process_augustin_file(save_path_for_pdf, path_to_new_directory, plugin_utility):
    """Process the Augustin file."""

    # split file in single pages
    plugin_utility.save_pdf_a3_to_pdf_a4(save_path_for_pdf, path_to_new_directory)

    src = fitz.open(save_path_for_pdf)

    # extract version number from directory name
    version_number = plugin_utility.extract_version_number(path_to_new_directory)

    # check if the version number exists already as papers category
    # if not, create it

    papers_category_id = check_for_papers_category(version_number)
    if not papers_category_id:
        papers_category_id = create_papers_category(version_number)
        print(f"papers_category_id: {papers_category_id}")

    categories = []
    meta_array = {
        "category": 0,
        "image_id": "",
        "image_text": "",
        "raw_text": "",
        "headlines": [],
        "starting_characters": [],
        "first_page_image_id": "",
        "category_papers": papers_category_id,  # ausgabennummer
    }
    print(f"meta_array: {meta_array}")
    next_page_needed = False

    for index, page in enumerate(src):

        # skip first page
        if index == 0:
            meta_array["first_page_image_id"] = plugin_utility.save_page_as_image(
                index, src, path_to_new_directory + "first_page.jpg"
            )
            continue
        print(f"parse page {index} of {len(src)} pages.")
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
        print("Main upload category", category)

        # Commented out the following lines leading to an error parsing images

        # Crop page if category is "editorial"
        # if category == "editorial":
        #     page = plugin_utility.crop_by_percentage_page(
        #         40, page, src, index, path_to_new_directory
        #     )

        print(
            f""" meta array category not equal 0: {meta_array['category'] != 0}
                and category: {category != meta_array['category']} and
                next_page_needed: {next_page_needed}"""
        )
        if (
            meta_array["category"] != 0
            and category != meta_array["category"]
            and next_page_needed
        ):
            # This is the case when the category has changed
            print("Category changed, so upload data now.", meta_array)
            meta_array["upload_data_now"] = True
            raw_text, headlines, starting_characters, next_page_needed = parse_page(
                page, meta_array
            )
            # Set meta array back to default
            meta_array["upload_data_now"] = False
            # This is the case when the page has been uploaded
            print("Reset meta_array")
            meta_array = {
                "category": 0,
                "image_id": "",
                "image_text": "",
                "index": 0,
                "raw_text": "",
                "headlines": [],
                "starting_characters": [],
                "category_papers": papers_category_id,  # ausgabennummer
            }

        number_of_images, image_id, image_text, gustl_wp_id = parse_image(
            page, src, index, path_to_new_directory
        )
        if gustl_wp_id is not None:
            print(f"Uploading post with gustl_wp_id: {gustl_wp_id}")
            meta = {
                "protocol": "",
                "photograph": "",
                "title": "Gustl",
                "author": "",
                "category": category,
                "category_papers": papers_category_id,
            }
            requests.upload_post(meta, "", gustl_wp_id)

        if number_of_images == 0:
            print(f"Main upload No image found on page {index}")
            # Get sample image_id from env file
            image_id = os.environ.get("SAMPLE_IMAGE_ID")

        meta_array["image_id"] = image_id
        meta_array["image_text"] = image_text
        # Set new or same category in meta array
        meta_array["category"] = category
        print("Entering parse page once meta_array:")

        # Editorial handling
        if category == "editorial":
            # Editorial should have the first page as thumbnail
            meta_array["image_id"] = meta_array["first_page_image_id"]
            # Crop page if category is "editorial"
            page = plugin_utility.crop_by_percentage_page(
                40, page, src, index, path_to_new_directory
            )

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
        print("Reset meta_array")
        meta_array = {
            "category": 0,
            "image_id": "",
            "image_text": "",
            "index": 0,
            "raw_text": "",
            "headlines": [],
            "starting_characters": [],
            "category_papers": papers_category_id,  # ausgabennummer
        }

        # DTodo: set the cover as image for the main item in the augustin backend # noqa: E501
        # DTodo: set the color code in the settings of the augustin backend # noqa: E501
    src.close()
