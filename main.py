"""Main function of the FastAPI application."""
import traceback

import fitz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from utils import requests
from utils.text_parser import create_meta_information, get_raw_text
from utils.utils import PluginUtility

app = FastAPI()


@app.get("/")
async def main():
    """HTML form to upload a file."""
    content = """
    <body>
    <form action='/upload' enctype='multipart/form-data' method='post'>
    <input name='file' type='file'>
    <input type='submit'>
    </form>
    </body>
    """
    return HTMLResponse(content=content)


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    """Upload file endpoint."""

    # create instance of PluginUtility
    plugin_utility = PluginUtility()

    try:
        save_path_for_pdf, path_to_new_directory = plugin_utility.upload_file(file)
    except IOError as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()
        try:
            # split file in single pages
            plugin_utility.save_pdf_a3_to_pdf_a4(
                save_path_for_pdf, path_to_new_directory
            )

            src = fitz.open(save_path_for_pdf)

            categories = []
            for index, page in enumerate(src):
                # skip first page
                if index == 0:
                    continue

                category = plugin_utility.identify_category(
                    page, index, path_to_new_directory
                )
                categories.append(category)

                # Try extracting raw text from page with exception handling
                try:
                    raw_text = get_raw_text(page)
                except IOError as e:
                    traceback.print_exc()
                    error_message = f"Error extracting raw text: {e}"
                    raise IOError(error_message) from e

                # Try posting raw text and category to Wordpress backend with exception handling
                try:
                    meta_information = create_meta_information(category)
                    response = requests.upload_post(meta_information, raw_text, "")
                except IOError as e:
                    traceback.print_exc()
                    error_message = f"WPLocal not running? No connection established uploading from main: {e}"
                    raise IOError(error_message) from e

                if response.status_code not in [200, 201]:
                    raise IOError(
                        f"Error posting to Wordpress: {response.content} with status code {response.status_code}"
                    )

                # DTodo: create post with type papers and the name of the issue # noqa: E501
                # DTodo: create new term in category "papers" with the name of the issue # noqa: E501
                # DTodo: create new keycloak role with the name of the issue
                # DTodo: set the cover as image for the main item in the augustin backend # noqa: E501
                # DTodo: set the color code in the settings of the augustin backend # noqa: E501

        except IOError as e:
            traceback.print_exc()
            error_message = f"Final error catchment: {e}"
            raise IOError(error_message) from e

    return {
        "message": f"Successfully uploaded {file.filename}",
        "categories": categories,
    }
