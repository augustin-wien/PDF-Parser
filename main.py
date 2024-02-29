"""Main function of the FastAPI application."""

import os
import traceback

import fitz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from utils import requests
from utils.parser import parse_image, parse_page
from utils.requests import check_for_papers_category, create_papers_category
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

    # Run check for PDF
    plugin_utility.pdf_check(file)

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
            meta_array = {
                "category": 0,
                "image_id": "",
                "image_text": "",
                "raw_text": "",
                "headlines": [],
                "starting_characters": [],
                "first_page_image_id": "",
                "category_papers": papers_category_id,  # ausgabennummer
            }
            print(f"meta_array: {meta_array}")
            next_page_needed = False

            for index, page in enumerate(src):

                # skip first page
                if index == 0:
                    meta_array["first_page_image_id"] = (
                        plugin_utility.save_page_as_image(
                            index, src, path_to_new_directory
                        )
                    )
                    continue
                print(f"parse page {index} of {len(src)} pages.")
                # Identify category of page
                try:
                    category = plugin_utility.identify_category(
                        page, index, path_to_new_directory
                    )
                    categories.append(category)

                except IOError as e:
                    traceback.print_exc()
                    error_message = f"Error identifying category: {e}"
                    raise IOError(error_message) from e
                print("Main upload category", category)

                # Commented out the following lines leading to an error parsing images

                # Crop page if category is "editorial"
                # if category == "editorial":
                #     page = plugin_utility.crop_by_percentage_page(
                #         40, page, src, index, path_to_new_directory
                #     )

                print(
                    f""" meta array category not equal 0: {meta_array['category'] != 0}
                      and category: {category != meta_array['category']} and
                      next_page_needed: {next_page_needed}"""
                )
                if (
                    meta_array["category"] != 0
                    and category != meta_array["category"]
                    and next_page_needed
                ):
                    # This is the case when the category has changed
                    print("Category changed, so upload data now.", meta_array)
                    meta_array["upload_data_now"] = True
                    raw_text, headlines, starting_characters, next_page_needed = (
                        parse_page(page, meta_array)
                    )
                    # Set meta array back to default
                    meta_array["upload_data_now"] = False
                    # This is the case when the page has been uploaded
                    print("Reset meta_array")
                    meta_array = {
                        "category": 0,
                        "image_id": "",
                        "image_text": "",
                        "index": 0,
                        "raw_text": "",
                        "headlines": [],
                        "starting_characters": [],
                        "category_papers": papers_category_id,  # ausgabennummer
                    }

                number_of_images, image_id, image_text, gustl_wp_id = parse_image(
                    page, src, index, path_to_new_directory
                )
                if gustl_wp_id is not None:
                    print(f"Uploading post with gustl_wp_id: {gustl_wp_id}")
                    meta = {
                        "protocol": "",
                        "photograph": "",
                        "title": "Gustl",
                        "author": "",
                        "category": category,
                        "category_papers": papers_category_id,
                    }
                    requests.upload_post(meta, "", gustl_wp_id)

                if number_of_images == 0:
                    print(f"Main upload No image found on page {index}")
                    # Get sample image_id from env file
                    image_id = os.environ.get("SAMPLE_IMAGE_ID")

                meta_array["image_id"] = image_id
                meta_array["image_text"] = image_text
                # Set new or same category in meta array
                meta_array["category"] = category
                print("Entering parse page once meta_array:")

                # Editorial handling
                if category == "editorial":
                    # Editorial should have the first page as thumbnail
                    meta_array["image_id"] = meta_array["first_page_image_id"]
                    # Crop page if category is "editorial"
                    page = plugin_utility.crop_by_percentage_page(
                        40, page, src, index, path_to_new_directory
                    )

                raw_text, headlines, starting_characters, next_page_needed = parse_page(
                    page, meta_array
                )
                if next_page_needed:
                    print("Next page needed")
                    # This case occurs when the page has its end on the next pages
                    meta_array["raw_text"] = " ".join(meta_array["raw_text"]) + raw_text
                    meta_array["headlines"] += headlines
                    meta_array["starting_characters"] += starting_characters

                    continue

                # This is the case when the page has been uploaded
                print("Reset meta_array")
                meta_array = {
                    "category": 0,
                    "image_id": "",
                    "image_text": "",
                    "index": 0,
                    "raw_text": "",
                    "headlines": [],
                    "starting_characters": [],
                    "category_papers": papers_category_id,  # ausgabennummer
                }

                # DTodo: create post with type papers and the name of the issue # noqa: E501
                # DTodo: create new term in category "papers" with the name of the issue # noqa: E501
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
