"""Extracts the text from the third page of the PDF file."""

# Modules for PDF extraction -> PyMuPDF
import base64

# Modules for Wordpress REST API
import json

import fitz
import requests


def upload_image(image):

    url = "http://localhost:10008/wp-json/wp/v2/media"

    user = "lebe"
    password = "vGSP ZpDr u1yy r8OH pZ54 Scjp"

    credentials = user + ":" + password

    token = base64.b64encode(credentials.encode())

    header = {"Authorization": "Basic " + token.decode("utf-8")}

    media = {
        "file": open("new_image.jpeg", "rb"),
        "caption": "first_try",
    }

    response = requests.post(url, headers=header, files=media)

    image_id = json.loads(response.content)["id"]

    return image_id


def create_post(image_id, page):
    """Creates a post with the extracted text and the uploaded image."""
    # here, text file is in CORRECTLY ORDERED inone big string
    text = page.get_text("text")
    # to have a list containing each line I save the whole text
    with open("page3.txt", "w") as f:
        f.write(text)
    # next I open it again
    with open("page3.txt") as f:
        lines = f.readlines()
    # to get all the metadata I focus on the word "PROTOKOLL:"
    # Sample output of print(lines) looking like this
    # ['570\n', '3\n', 'augustiner:in\n', 'Bernd Pegritz \n', '«Rätsel» lösen mit Bildern\n', 'PROTOKOLL: SÓNIA MELO \n', 'FOTO: MARIO LANG\n',  'A\n',...]
    return_values = []
    # Define main dict to input required parameters for post
    post_dict = {}
    for i, line in enumerate(lines):
        if "PROTOKOLL:" in line:
            # post_dict['protocol'] = lines[i]
            # post_dict['photograph'] = lines[i + 1]
            post_dict["title"] = lines[i - 1]
            # post_dict["author"] = lines[i - 2]
            post_dict["author"] = 1
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
    # As shown, newlines have to be removed correctly i.e. not if a dot is before
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
                print("supposed to be a dot or !", letter)
            else:
                del article_edit[index]
        # deletes double spaces
        if " " in letter and " " in article[index - 1]:
            del article_edit[index]
        # deletes hyphen if not set on purpose
        if "-" in letter:
            if " " in article[index - 1] and " " in article[index + 1]:
                # this hyphen has been set on purpose and stays
                print("hyphen has been set on purpose")
            else:
                # deletes hyphen on the index and the extra space before it
                del article_edit[index]
                del article_edit[index - 1]

    # to create a readable text for the article
    art = ""
    for letter in article_edit:
        art += letter

    post_dict["content"] = art
    # post_dict["featured_media"] = image_id
    post_dict["status"] = "publish"
    post_dict["post_type"] = "post"

    ### POST REQUEST ###

    url = "http://localhost:10008/wp-json/wp/v2/media"

    user = "lebe"
    password = "vGSP ZpDr u1yy r8OH pZ54 Scjp"

    credentials = user + ":" + password

    token = base64.b64encode(credentials.encode())

    header = {"Authorization": "Basic " + token.decode("utf-8")}

    post2 = {
        "date": "2023-06-19T20:00:35",
        "title": "hey this is the title",
        "status": "publish",
        "content": "damn this is the content post",
        "author": "1",
        "excerpt": "Exceptional post!",
        "post_type": "post",
    }

    response = requests.post(url, headers=header, json=post2)

    print("response", response.content)


src = fitz.open("../PyMuPDF/570_augustin_fertig_kontrolle.pdf")
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

# To check if page is correctly cropped, uncomment code to create new PDF
new_doc.save(
    "new" + src.name.split(".")[2].split("/")[2] + ".pdf",
    garbage=3,
    deflate=True,
)

doc = fitz.open("new" + src.name.split(".")[2].split("/")[2] + ".pdf")
new_page = doc.load_page(0)


# Get image from PDF
images = new_page.get_images()
# get specific xref we want

# for loop to see where wanted image is located
# for i, img in enumerate(images):
#     xref = img[0]
#     image = new_doc.extract_image(xref)
#     # write extracted image to file
#     imgout = open(f"new_image{i}_{img[0]}.{image['ext']}", "wb")
#     imgout.write(image["image"])
#     imgout.close()


xref = images[-1][0]
image = new_doc.extract_image(xref)

# write extracted image to file
imgout = open(
    # f"new_image_{xref}_{src.name.split('.')[2].split('/')[2]}.{image['ext']}", "wb"
    f"new_image.{image['ext']}",
    "wb",
)
imgout.write(image["image"])
imgout.close()

id = upload_image(image)
print("Image uploaded successfully!", id)

create_post(id, new_page)
