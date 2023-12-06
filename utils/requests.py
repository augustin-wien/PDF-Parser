"""Send requests to Wordpress API."""
import base64
import json
import os

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

    media = {"file": open(image_path, "rb"), "caption": image_title}

    response = requests.post(url, headers=header, files=media, timeout=5)

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

    header = generate_auth_header()

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
        if cat["name"].strip() == category.strip():
            return cat["id"]

    # if category does not exist, return category "Uncategorized", which has always id 1
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
        "post_type": "articles",
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
