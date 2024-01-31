"""Playground for uploading several images with Wordpress API."""

import json
import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from utils.requests import generate_auth_header

load_dotenv()

global_url = os.environ.get("WORDPRESS_URL")


def upload_image(image_path, image_title):
    """Upload the image to the Wordpress media library."""
    url = global_url + "media"

    header = generate_auth_header()

    with open(image_path, "rb") as file:
        media = {"file": file, "caption": image_title}

        response_playground = requests.post(url, headers=header, files=media, timeout=5)

    if response_playground.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail="Image could not be uploaded!"
            + str(response_playground.status_code)
            + str(response_playground.content),
        )

    print(f"response content {response_playground.content}")

    image_id_playground = json.loads(response_playground.content)["id"]
    image_src_playground = json.loads(response_playground.content)["media_details"][
        "sizes"
    ]["full"]["source_url"]

    return image_id_playground, image_src_playground


def upload_post(meta_information_pg, readable_text_pg, image_id_pg):
    """Upload the post via the Wordpress API."""
    url = global_url + "posts"

    header = generate_auth_header()

    post = {
        "title": meta_information_pg["title"],
        "status": "publish",
        "content": readable_text_pg,
        "excerpt": meta_information_pg["author"]
        + " "
        + meta_information_pg["photograph"]
        + " "
        + meta_information_pg["protocol"],
        "post_type": "articles",
        "featured_media": image_id_pg,
    }

    response_pg = requests.post(url, headers=header, json=post, timeout=5)

    if response_pg.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail="Post could not be uploaded!"
            + str(response_pg.status_code)
            + str(response_pg.content),
        )

    return response_pg


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
