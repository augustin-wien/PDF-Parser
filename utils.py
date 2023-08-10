"""Common utility functions for the plugin."""
import base64
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

global_path = os.environ.get("AUGUSTIN_PLUGIN_PATH")
global_url = os.environ.get("AUGUSTIN_PLUGIN_URL")


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
