"""Main function of the FastAPI application."""
import os
import traceback

import fitz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

# from parsers.extract_page_0 import save_page_0_as_image
# from parsers.extract_page_1 import extract_page
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
            # split file in single pages and save them as pdf
            number_of_pages = plugin_utility.split_pdf_a3_to_a4(
                save_path_for_pdf, path_to_new_directory
            )

            # takes range of index starting at 1 and ending at index
            for index in range(1, number_of_pages):
                print(f"Extracting page {index}")
                path_to_page = os.path.join(path_to_new_directory, f"page-{index}.pdf")
                print("Path to page", path_to_page)
                src = fitz.open(path_to_page)
                page = src.load_page(0)
                category = plugin_utility.identify_category(page, index)
                print(category)

        except IOError as e:
            traceback.print_exc()
            error_message = f"Error extracting: {e}"
            raise IOError(error_message) from e
    response = "empty"
    return {"message": f"Uploaded {file.filename} and post {response}"}
