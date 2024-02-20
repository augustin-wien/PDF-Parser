"""Main function of the FastAPI application."""

import os
import traceback

import fitz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from utils.parser import parse_image, parse_page
from utils.requests import check_for_papers_category, create_papers_category, save_page_as_image
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
        traceback.print_exc()
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()
        try:
            # split file in single pages
            plugin_utility.save_pdf_a3_to_pdf_a4(
                save_path_for_pdf, path_to_new_directory
            )

            src = fitz.open(save_path_for_pdf)

            # extract version number from directory name
            version_number = plugin_utility.extract_version_number(
                path_to_new_directory
            )

            # check if the version number exists already as papers category
            # if not, create it

            papers_category_id = check_for_papers_category(version_number)
            if not papers_category_id:
                papers_category_id = create_papers_category(version_number)
                print(f"papers_category_id: {papers_category_id}")

            categories = []

            meta_array = initMetaArray(papers_category_id)
            # identify category of each page
            for index, page in enumerate(src):
                # skip first page
                if index == 0:
                    continue

                try:
                    category = plugin_utility.identify_category(
                        page, index, path_to_new_directory
                    )
                    categories.append(category)

                except IOError as e:
                    traceback.print_exc()
                    error_message = f"Error identifying category: {e}"
                    raise IOError(error_message) from e
        

            for index, page in enumerate(src):

                # skip first page
                if index == 0:
                    continue

                print(f"parse page {index} of {len(src)} pages.")
                # Identify category of page
                category = categories[index - 1]
                print("category", category)
                number_of_images, image_id, image_text = parse_image(
                    page, src, index, path_to_new_directory
                )

                if number_of_images == 0:
                    # Get sample image_id from env file
                    image_id = os.environ.get("SAMPLE_IMAGE_ID")

                meta_array["category"] = category
                meta_array["image_text"] = image_text

                if category == "editorial":
                    # Extract first page as image if category is editorial
                    image_id = None
                    try:
                        image_id = save_page_as_image(0, src, path_to_new_directory)
                        print("image_id for editorial", image_id)
                    
                    except IOError as e:
                        traceback.print_exc()
                        error_message = f"Error extracting and uploading images: {e}"
                        raise IOError(error_message) from e

                meta_array["image_id"] = image_id

                # check if the next page has a different category to force the current page to be uploaded
                next_page_category = categories[index] if index < len(categories) else None
                print("next_page_category", next_page_category)

                force_upload = False
                if next_page_category and next_page_category != category:
                    force_upload = True

                raw_text, headlines, starting_characters, next_page_needed = parse_page(
                    page, meta_array, force_upload
                )
                if next_page_needed and not force_upload:
                    print("Next page needed")
                    # This case occurs when the page has its end on the next pages
                    meta_array["raw_text"] = " ".join(meta_array["raw_text"]) + raw_text
                    meta_array["headlines"] += headlines
                    meta_array["starting_characters"] += starting_characters

                    continue

                # This is the case when the page has been uploaded
                print("Reset meta_array")
                meta_array = initMetaArray(papers_category_id)

                # DTodo: create new keycloak role with the name of the issue
                # DTodo: set the cover as image for the main item in the augustin backend # noqa: E501
                # DTodo: set the color code in the settings of the augustin backend # noqa: E501
            src.close()
        except IOError as e:
            traceback.print_exc()
            error_message = f"Final error catchment: {e}"
            raise IOError(error_message) from e

    return {
        "message": f"Successfully uploaded {file.filename}",
        "categories": categories,
    }

def initMetaArray(papers_category_id):
    meta_array = {
        "category": 0,
        "image_id": "",
        "image_text": "",
        "raw_text": "",
        "index": 0,
        "headlines": [],
        "starting_characters": [],
        "category_papers": papers_category_id,  # ausgabennummer
    }
    return meta_array