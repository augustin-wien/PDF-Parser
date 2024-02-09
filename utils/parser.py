"""Parsing functions to extract images and text from PDF."""

import traceback

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


def clean_text(article):
    """Clean the text from unwanted newlines and hyphens."""
    # Format the string
    article = list(article)
    article_edit = article
    for index, letter in enumerate(article):
        if " " in letter and " " in article[index - 1]:
            del article_edit[index]

    return "".join(article_edit)


def extract_headlines(page):
    """Extract headlines from a PDF page."""
    headlines = []
    starting_characters = []
    ending_symbols = 0
    text_instances = page.get_text("dict", sort=True)["blocks"]

    if not text_instances:
        return headlines

    for text in text_instances:
        try:
            for line in text["lines"]:
                for span in line["spans"]:
                    font_size = span["size"]
                    colour_code = f"#{span['color']:06x}"

                    # Check if colour code is not black or dark brown since starting characters have version colour
                    if colour_code != "#2e2013" and colour_code != "#000000":
                        # ------ Starting characters check ------
                        # Check if text is not a number, has less than 3 characters and is not ending character
                        if (
                            not span["text"].isdigit()
                            and len(span["text"]) < 3
                            and span["text"] != "■"
                        ):
                            print(f"Extracting starting character: {span['text']}")
                            starting_characters.append(span["text"].strip())
                        # ------ Ending symbol check ------
                        elif "■" in span["text"]:
                            print(f"Extracting ending symbol: {span['text']}")
                            ending_symbols += 1

                    # ------ Header check ------
                    # Check if font is bold and font size is larger 12
                    elif (
                        "bold" in span["font"].lower()
                        and font_size > 12
                        or font_size > 15
                        or span["font"] == "AmasisMTStd-Bold"
                    ):
                        headlines.append(span["text"].strip())

        except KeyError:
            pass

    return headlines, starting_characters, ending_symbols


# Function returns all the text from the given PDF page
def extract_text(page):
    """Get the raw text from the PDF page."""
    # get raw text from page
    raw_text = page.get_text()

    # 1. Step: Check for headline and starting characters
    headlines, starting_characters, ending_symbols = extract_headlines(page)

    # 2. Step: Check for all options
    article, headline = "", ""
    # 2.1 Option: Exactly one story on page
    print(
        f"""Length of headlines: {len(headlines)},
        starting characters: {len(starting_characters)},
        ending symbols: {ending_symbols}"""
    )
    if len(headlines) >= 1 and len(starting_characters) >= 1 and ending_symbols == 1:
        # Iterate through all lines and extract article text
        found_starting_character = False

        # Join all headlines to one string
        headline = " ".join(headlines)

        for line in raw_text.split("\n"):
            if found_starting_character:
                if "■" in line:
                    found_starting_character = False
                    break
                # Clean text from unwanted hyphens and add newlines, if line is not empty
                if line:
                    # If in the end of line is "." or "!" or "?" or ":" keep newline
                    if line[-1] in [".", "!", "?", ":"]:
                        print(f"Article before ending symbol: {article}")
                        print(f"Found line with ending symbol: {line}")
                        article += line + "\n"
                        print(f"Article after ending symbol: {article}")
                        continue
                    # If in the end of line is "-" delete hyphen and extra space before it
                    elif line and line[-1] == "-":
                        print(f"Article before hyphen: {article}")
                        print(f"Found line with hyphen: {line}")
                        article += line[:-1]
                        print(f"Article after hyphen: {article}")
                        continue
                # If no checks are met, add line to article
                article += line
            # Start extracting article text with first starting character
            if starting_characters[0] == line:
                article += line
                found_starting_character = True

    # 3. Step: Save text into variable from header to ending symbol

    return raw_text, article, headline


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


def parse_page(page, category, image_text, image_id):
    """Parse a single page of a PDF file and upload it to the Wordpress backend."""

    # Extract raw text from page with exception handling
    try:
        raw_text, article, headline = extract_text(page)
    except IOError as e:
        traceback.print_exc()
        error_message = f"Error extracting raw text: {e}"
        raise IOError(error_message) from e

    # Try posting raw text and category to Wordpress backend with exception handling
    try:
        meta_information = create_meta_information(category, headline)

        # If article is not empty, set raw_text to article
        if article:
            article = clean_text(article)
            raw_text = article

        # Append image_text to raw_text
        raw_text += image_text

        # Post to Wordpress
        response = requests.upload_post(meta_information, raw_text, image_id)
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
