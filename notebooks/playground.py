import base64
import json
import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

global_url = os.environ.get("WORDPRESS_URL")


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

    print(f"response content {response.content}")

    image_id = json.loads(response.content)["id"]
    image_src = json.loads(response.content)["media_details"]["sizes"]["full"][
        "source_url"
    ]

    return image_id, image_src


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


def upload_post(meta_information, readable_text, image_id):
    """Upload the post via the Wordpress API."""
    url = global_url + "posts"

    header = generate_auth_header()

    post = {
        "title": meta_information["title"],
        "status": "publish",
        "content": readable_text,
        "excerpt": meta_information["author"]
        + " "
        + meta_information["photograph"]
        + " "
        + meta_information["protocol"],
        "post_type": "articles",
        "featured_media": image_id,
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


image_id, image_src = upload_image("/home/funny/Pictures/leon.jpg", "Leon.jpg")

readable_text = f"""
Plumpes Zeugnis der Unfähigkeit
<!-- wp:image "id":{image_id},"sizeSlug":"full","linkDestination":"none" -->
<figure class="wp-block-image size-full"><img src="{image_src}" alt="" class="wp-image-{image_id}"/></figure>
<!-- /wp:image -->
"""

meta_information = {
    "title": "Multiple images",
    "author": "Leon",
    "photograph": "Leon",
    "protocol": "Leon",
}

response = upload_post(meta_information, readable_text, image_id)

print(response.status_code)
