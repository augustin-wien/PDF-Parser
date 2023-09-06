"""Main function of the FastAPI application."""
import os

from dotenv import load_dotenv
from parsers.extract_page_0 import save_page_0_as_image
from parsers.extract_page_1 import extract_page
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

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
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()
        try:

            # extract page 0 from file -> Cover page
            save_page_0_as_image(save_path)



            # extract page 3 from file
            response = extract_page(save_path)

        except Exception as e:
            return {"message": f"Error extracting: {e}"}

    return {"message": f"Uploaded {file.filename} and post {response}"}
