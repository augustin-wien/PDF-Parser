"""Main function of the FastAPI application."""
import os
import traceback

import fitz
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from parsers.extract_page_0 import save_page_0_as_image
from parsers.extract_page_1 import extract_page
from utils.utils import identify_category, split_pdf_a3_to_a4

load_dotenv()

global_path = os.environ.get("AUGUSTIN_PLUGIN_SAVE_PATH")

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
    try:
        save_path = os.path.join(global_path, file.filename)
        with open(save_path, "wb") as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except IOError as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()
        try:
            # split file in single pages
            split_pdf_a3_to_a4(save_path)

            # identify pages
            src = fitz.open(save_path)
            i = 0
            for page in src:
                if i == 0:
                    i = i + 1
                    # extract page 0 from file -> Cover page
                    save_page_0_as_image(save_path)
                    # DTodo: create post with type papers and the name of the issue # noqa: E501
                    # DTodo: create new term in category "papers" with the name of the issue # noqa: E501
                    # DTodo: create new keycloak role with the name of the issue
                    # DTodo: set the cover as image for the main item in the augustin backend # noqa: E501
                    # DTodo: set the color code in the settings of the augustin backend # noqa: E501
                    continue
                category = identify_category(page, i)
                print(i, category)
                i = i + 1
                if category.strip() == "augustiner:in":
                    # extract einsicht article text from file
                    response = extract_page(save_path, category)

        except IOError as e:
            traceback.print_exc()
            error_message = f"Error extracting: {e}"
            raise IOError(error_message) from e

    return {"message": f"Uploaded {file.filename} and post {response}"}
