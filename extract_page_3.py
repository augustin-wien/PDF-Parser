"""Extracts the text from the third page of the PDF file."""

# Modules for PDF extraction -> PyMuPDF
import base64

# Modules for Wordpress REST API
import json
import os

import fitz
import requests

# TODO remove hardcoded values
global_path = (
    "/home/funny/Documents/Projects/230701-Parsing-Tool/augustin-plugin/sample_data/"
)
global_url = "http://localhost:10004/wp-json/wp/v2/"


def create_post(page, image_id):
    """Create a post with the extracted text and the uploaded image."""
    # First, create rect for article text which is on the bottom third of page
    r = page.rect
    r.y0 = (r.y1 * 2) / 3  # two third of page height
    article = page.get_textbox(r)

    # Second, create rect for article title which is in between half and third bottom of page
    r2 = page.rect
    r2.y0 = r2.y1 / 2  # half of page height
    r2.y1 = r2.y1 * 2 / 3 - 3  # two third of page height -3 so it is not overlapping
    meta_string = page.get_textbox(r2)
    meta_array = meta_string.splitlines()

    # WARNING: This is not dynamic and only relies on the word "protokoll"
    # Assign meta data to variables
    for i, line in enumerate(meta_array):
        if "protokoll:" in line.lower():
            protocol = meta_array[i].lower().title()
            photograph = meta_array[i + 1].lower().title()
            title = meta_array[i - 1]
            author = "Autor*in: " + meta_array[i - 2].lower().title()

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
    readable_text = ""
    for letter in article_edit:
        readable_text += letter

    # POST REQUEST #

    url = global_url + "posts"

    user = "lebe"
    password = "gUwM J4pU sngD VHpk Cub7 quS2"

    credentials = user + ":" + password

    token = base64.b64encode(credentials.encode())

    header = {"Authorization": "Basic " + token.decode("utf-8")}

    post = {
        "title": title,
        "status": "publish",
        "content": readable_text,
        "excerpt": author + " " + photograph + " " + protocol,
        "post_type": "post",
        "featured_media": image_id,
    }

    response = requests.post(url, headers=header, json=post)

    print("response", response.content)

    return response.content


def download_image(page, doc, src):
    """Download the image from the PDF file."""
    # Get image from PDF
    img_list = page.get_images(full=True)

    # iterate through image list to get single xref with positive values
    for img in img_list:
        i = 0
        rect = page.get_image_bbox(img)
        if rect[0] > 0 and rect[1] > 0 and rect[2] > 0 and rect[3] > 0:
            xref = img[0]  # get specific xref we want
            i += 1

    if i > 1:
        print("Warning: More than one image found on page 3")
    elif i == 1:
        image = doc.extract_image(xref)
    else:
        print("Warning: No image found on page 3")

    # TODO delete manual path definition
    # write extracted image to file
    image_title = src.name.split(".")[0] + "_image_" + str(xref)
    image_path = os.path.join(
        global_path,
        image_title + "." + image["ext"],
    )
    with open(
        (image_path),
        "wb",
    ) as imgout:
        imgout.write(image["image"])
        imgout.close()

    image_id = upload_image(image_path, image_title)

    return image_id


def upload_image(image_path, image_title):
    """Upload the image to the Wordpress media library."""
    url = global_url + "media"

    user = "lebe"
    password = "gUwM J4pU sngD VHpk Cub7 quS2"

    credentials = user + ":" + password

    token = base64.b64encode(credentials.encode())

    header = {"Authorization": "Basic " + token.decode("utf-8")}

    media = {"file": open(image_path, "rb"), "caption": image_title}

    response = requests.post(url, headers=header, files=media)

    image_id = json.loads(response.content)["id"]

    return image_id


def extract_page(pfd_file):
    """Extract the text from the third page of the PDF file."""
    src = fitz.open(pfd_file)
    new_doc = fitz.open()  # empty output PDF

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
    new_page = new_doc.new_page(-1, width=r2.width, height=r2.height)
    new_page.show_pdf_page(
        new_page.rect,
        src,
        page.number,
        clip=r2,
    )

    image_id = download_image(new_page, new_doc, src)

    response = create_post(new_page, image_id)

    return response
