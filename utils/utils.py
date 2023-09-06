"""Common utility functions for the plugin."""
import base64
import json
import os

import requests
from dotenv import load_dotenv

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

def upload_image(image_path, image_title):
    """Upload the image to the Wordpress media library."""
    url = global_url + "media"

    header = generate_auth_header()    

    media = {"file": open(image_path, "rb"), "caption": image_title}

    response = requests.post(url, headers=header, files=media)

    image_id = json.loads(response.content)["id"]

    return image_id
