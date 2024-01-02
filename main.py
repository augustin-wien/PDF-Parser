"""Main function of the FastAPI application."""
import traceback

import fitz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
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
        print(f"Save path for pdf: {save_path_for_pdf}")
        print(f"Path to new directory: {path_to_new_directory}")
    except IOError as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()
        try:
            # split file in single pages
            plugin_utility.save_pdf_a3_to_pdf_a4(
                save_path_for_pdf, path_to_new_directory
            )
            # split file in single pages and save them as pdf
            number_of_pages = plugin_utility.split_pdf_to_single_pdfs(
                save_path_for_pdf, path_to_new_directory
            )
            print(f"Number of pages: {number_of_pages}")

            src = fitz.open(save_path_for_pdf)

            for index, page in enumerate(src):
                # skip first page
                if index == 0:
                    continue

                category = plugin_utility.identify_category(
                    page, index, path_to_new_directory
                )
                print(f"Category: {category}")
                # DTodo: create post with type papers and the name of the issue # noqa: E501
                # DTodo: create new term in category "papers" with the name of the issue # noqa: E501
                # DTodo: create new keycloak role with the name of the issue
                # DTodo: set the cover as image for the main item in the augustin backend # noqa: E501
                # DTodo: set the color code in the settings of the augustin backend # noqa: E501
                # if category.strip() == "augustiner:in":
                #     # extract einsicht article text from file
                #     response = extract_page(save_path_for_pdf, category)

        except IOError as e:
            traceback.print_exc()
            error_message = f"Error extracting: {e}"
            raise IOError(error_message) from e

    return {"message": f"Successfully uploaded {file.filename}"}
