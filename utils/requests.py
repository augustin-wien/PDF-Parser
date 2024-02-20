"""Send requests to Wordpress API."""

import base64
import json
import os
import traceback

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

global_url = os.environ.get("WORDPRESS_URL")
debug = os.environ.get("DEBUG")


def generate_auth_header():
    """Generate the authentication header for the Wordpress API."""
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


def upload_image(image_path, image_title):
    """Upload the image to the Wordpress media library."""
    url = global_url + "media"

    header = generate_auth_header()

    with open(image_path, "rb") as file:
        media = {"file": file, "caption": image_title}

        response = requests.post(url, headers=header, files=media, timeout=5)

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail="Image could not be uploaded!"
            + str(response.status_code)
            + str(response.content),
        )

    image_id = json.loads(response.content)["id"]
    try:
        src = json.loads(response.content)["media_details"]["sizes"]["full"][
            "source_url"
        ]
    except KeyError:
        pass
    try:
        src = json.loads(response.content)["source_url"]
    except KeyError as e:
        traceback.print_exc()
        error_message = f"No image source url found: {e}"
        raise IOError(error_message) from e

    return image_id, src


def check_for_category(category):
    """
    Check if the category exists and return it.
    Return Uncategorized if not.
    """

    url = global_url + "categories?per_page=100"

    header = generate_auth_header()

    # Try receiving the categories with exception handling
    try:
        response = requests.get(url, headers=header, timeout=5)
    except IOError as e:
        traceback.print_exc()
        error_message = f"WPLocal not running? Error receiving a get request: {e}"
        raise IOError(error_message) from e

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail="Category could not be checked!"
            + str(response.status_code)
            + str(response.content),
        )

    category_list = json.loads(response.content)

    for cat in category_list:
        if category == "tun & lassen" and cat["name"].strip() == "tun &amp; lassen":
            return cat["id"]
        if cat["name"].strip() == category.strip():
            return cat["id"]

    # if category does not exist, return category "Uncategorized", which has always id 1
    return 1


def upload_post(meta_information, readable_text, image_id):
    """Upload the post via the Wordpress API."""
    url = global_url + "posts"

    header = generate_auth_header()

    category_number = check_for_category(meta_information["category"])

    post = {
        "title": meta_information["title"],
        "status": "publish",
        # WIP: Remove image_id once the image is uploaded to the media library
        "content": readable_text,
        "excerpt": meta_information["author"]
        + " "
        + meta_information["photograph"]
        + " "
        + meta_information["protocol"],
        "post_type": "articles",
        "featured_media": image_id,
        "categories": [category_number],
    }

    response = requests.post(url, headers=header, json=post, timeout=5)

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail="Post could not be uploaded!"
            + str(response.status_code)
            + str(response.content),
        )

    return response
