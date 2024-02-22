"""Main function of the FastAPI application."""

import traceback

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from utils.parser_augustin import process_augustin_file
from utils.parser_strawanzerin import Strawanzerin
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
        filename = file.filename.lower()
        if "augustin" in filename:
            file.file.close()
            try:
                process_augustin_file(
                    save_path_for_pdf, path_to_new_directory, plugin_utility
                )
            except IOError as e:
                traceback.print_exc()
                error_message = f"Final error catchment parsing Augustin file: {e}"
                raise IOError(error_message) from e
        else:
            strawanzerin = Strawanzerin()
            try:
                strawanzerin.parse_strawanzerin(
                    save_path_for_pdf, path_to_new_directory
                )
            except IOError as e:
                traceback.print_exc()
                error_message = f"Error parsing Strawanzerin: {e}"
                raise IOError(error_message) from e

    return {"message": f"Successfully uploaded {file.filename}"}
