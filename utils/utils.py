"""Common utility functions for the plugin."""
import base64
import json
import os
import fitz

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

global_path = os.environ.get("AUGUSTIN_PLUGIN_PATH")
global_url = os.environ.get("AUGUSTIN_PLUGIN_URL")
debug = os.environ.get("DEBUG")

def generate_auth_header():
    try:
        user = os.getenv("WP_API_USER")
        password = os.getenv("WP_API_KEY")

        credentials = user + ":" + password

        token = base64.b64encode(credentials.encode())

        header = {"Authorization": "Basic " + token.decode("utf-8")}
        return header
    except Exception as e:
        print(e, os.getenv("WP_API_USER"), os.getenv("WP_API_USER"))
        raise e


def get_header():
    """Get the header for the Wordpress API."""
    # if case for local development with localWP instance
    if "localhost:10004" in os.getenv("AUGUSTIN_PLUGIN_URL"):
        user = "lebe"
        password = "gUwM J4pU sngD VHpk Cub7 quS2"
    # normal case for production
    else:
        user = os.getenv("WP_API_USER")
        password = os.getenv("WP_API_PASSWORD")

    header = generate_auth_header()

    return header


def upload_image(image_path, image_title):
    """Upload the image to the Wordpress media library."""
    url = global_url + "media"

    header = get_header()

    media = {"file": open(image_path, "rb"), "caption": image_title}

    response = requests.post(url, headers=header, files=media)

    if (response.status_code != 200) and (response.status_code != 201):
        raise HTTPException(
            status_code=400,
            detail="Image could not be uploaded!"
            + str(response.status_code)
            + str(response.content),
        )

    image_id = json.loads(response.content)["id"]

    return image_id


def upload_post(title, readable_text, author, photograph, protocol, image_id, category):
    """Upload the post via the Wordpress API."""
    url = global_url + "posts"

    header = get_header()

    post = {
        "title": title,
        "status": "publish",
        "content": readable_text,
        "excerpt": author + " " + photograph + " " + protocol,
        "post_type": "articles",
        "featured_media": image_id,
        "categories": [category],
    }

    response = requests.post(url, headers=header, json=post)

    if (response.status_code != 200) and (response.status_code != 201):
        raise HTTPException(
            status_code=400,
            detail="Post could not be uploaded!"
            + str(response.status_code)
            + str(response.content),
        )

    return response


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

def get_size(filename):
    st = os.stat(filename)
    return st.st_size

def split_pdf_a3_to_a4(path_to_file):
    """Split the PDF file into single pages."""
    pdf_document = fitz.open(path_to_file)
    
    # Create a new PDF document for the output
    output_document = fitz.open()

    # Iterate through each page in the input PDF
    for spage in pdf_document:  # for each page in input
        if spage.rect.width < spage.rect.height:
            output_document.insert_pdf(pdf_document, from_page=spage.number, to_page=spage.number)
            continue

        r = spage.rect  # input page rectangle
        d = fitz.Rect(spage.cropbox_position,  # CropBox displacement if not
                      spage.cropbox_position)  # starting at (0, 0)
        # --------------------------------------------------------------------------
        # example: cut input page into 2 x 2 parts
        # --------------------------------------------------------------------------
        r1 = r   # top left rect
        r1.x1 /= 2  # half width
        r2 = r1 + (r1.width, 0, r1.width, 0)  # top right rect
        rect_list = [r1, r2]  # put them in a list

        for rx in rect_list:  # run thru rect list
            rx += d  # add the CropBox displacement
            page = output_document.new_page(-1,  # new output page with rx dimensions
                                width=rx.width,
                                height=rx.height)
            page.show_pdf_page(
                page.rect,  # fill all new page with the imageb
                pdf_document,  # input document
                spage.number,  # input page number
                clip=rx,  # which part to use of input page
            )
            #  Here we will convert the pdf to an image and check the size
            pix = page.get_pixmap()  # render page to an image
            name_png = f"page-{page.number}.png"  # _{random.randint(1,100)}
            pix.save(name_png)  # store image as a PNG
            imgsize = get_size(name_png)
            if not debug:
                os.remove(name_png)
            if imgsize < 1300:  #  A6 blank page size approximately 1209 Yours may be different, check first
                output_document.delete_page(pno=-1)
                break
    # Save the output PDF
    output_document.save(path_to_file)
    output_document.close()

# identify category of page
def identify_category(page, i):
    rect = fitz.Rect(60, 30, 200, 60)
    if i%2 == 0:
        rect = fitz.Rect(400, 30, 580, 60)
    left, top, right, bottom = rect
    if debug:
        pix = page.get_pixmap(clip=(left, top, right, bottom))
        name_png = f"page-{page.number}-category.png"
        pix.save(name_png)
    text_in_rect = ""
    for word in page.get_text("words"):
        x0, y0, x1, y1, text = word[:5]
        if left <= x0 <= right and top <= y0 <= bottom and left <= x1 <= right and top <= y1 <= bottom:
            text_in_rect += text + " "
    if text_in_rect == "":
        # maybe the category is on the side
        rect = fitz.Rect(10, 55, 80, 450)
        if i%2 == 0:
            rect = fitz.Rect(450, 55, 580, 350)
        left, top, right, bottom = rect
        if debug:
            pix = page.get_pixmap(clip=(left, top, right, bottom))
            name_png = f"page-{page.number}-category_side.png"
            pix.save(name_png)
        for word in page.get_text("words"):
            x0, y0, x1, y1, text = word[:5]
            if left <= x0 <= right and top <= y0 <= bottom and left <= x1 <= right and top <= y1 <= bottom:
                text_in_rect += text + " "
    if text_in_rect == "":
        text_in_rect = "Keine Kategorie gefunden" #propapblly full site advertisement
    # convert to downcase
    text_in_rect = text_in_rect.lower()
    # first page has a different structure
    if "editorial" in text_in_rect:
        text_in_rect = "editorial"
    return text_in_rect

