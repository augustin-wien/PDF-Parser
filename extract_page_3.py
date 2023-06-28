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
    # here, text file is in CORRECTLY ORDERED in one big string
    text = page.get_text("text")
    # to have a list containing each line I save the whole text
    with open("page3.txt", "w") as f:
        f.write(text)
    # next I open it again
    with open("page3.txt") as f:
        lines = f.readlines()
    # to get all the metadata I focus on the word "PROTOKOLL:"
    # Sample output of print(lines) looking like this
    # ['570\n', '3\n', 'augustiner:in\n', 'Bernd Pegritz \n',
    return_values = []
    for i, line in enumerate(lines):
        if "PROTOKOLL:" in line:
            protocol = lines[i]
            photograph = lines[i + 1]
            title = lines[i - 1]
            author = lines[i - 2]
            # this is where the article begins
            return_values.append(i + 2)

        if "■\n" in line:
            # searching for the ending dot to get the end of the article
            return_values.append(i)

    # this gives me the whole part of the article in single letters
    article = []
    for index in range(return_values[0], return_values[1]):
        article += lines[index]

    # print(article) gives me something like
    # ['A', '\n', 'n', 's', 't', 'a', 't', 't', ' ', 'd', 'i', 'e', ' '...]
    # As shown, newlines have to be removed correctly
    # i.e. not if a sentence ends

    # Format the string
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
    # Get all images from PDF
    images = page.get_images()

    # TODO delete manual xref definition
    # get specific xref we want
    xref = images[-1][0]
    image = doc.extract_image(xref)

    # TODO delete manual path definition
    # write extracted image to file
    print("src.name", src.name)
    print("src.name.split", src.name.split("."))
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
