"""Common utility functions for the plugin."""
import base64
import json
import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

global_path = os.environ.get("AUGUSTIN_PLUGIN_PATH")
global_url = os.environ.get("AUGUSTIN_PLUGIN_URL")

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


def check_for_category(category):
    """
    Check if the category exists and return it.
    Return Uncategorized if not.
    """

    url = global_url + "categories"

    header = get_header()

    response = requests.get(url, headers=header, timeout=5)

    if (response.status_code != 200) and (response.status_code != 201):
        raise HTTPException(
            status_code=400,
            detail="Category could not be checked!"
            + str(response.status_code)
            + str(response.content),
        )

    category_list = json.loads(response.content)

    for cat in category_list:
        if cat["name"] == category:
            return cat["id"]

    # if category does not exist, return Uncategorized, which has always id 1
    return 1


def upload_post(title, readable_text, author, photograph, protocol, image_id, category):
    """Upload the post via the Wordpress API."""
    url = global_url + "posts"

    header = generate_auth_header()

    category_number = check_for_category(category)

    post = {
        "title": title,
        "status": "publish",
        "content": readable_text,
        "excerpt": author + " " + photograph + " " + protocol,
        "post_type": "post",
        "featured_media": image_id,
        "categories": [category_number],
    }

    response = requests.post(url, headers=header, json=post, timeout=5)

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