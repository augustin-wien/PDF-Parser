"""Main function of the FastAPI application."""
from extract_page_3 import extract_page
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

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
        with open(file.filename, "wb") as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()
        # extract page 3 from file
        response = extract_page(file.filename)

    return {"message": f"Successfully uploaded {file.filename} and post {response}"}
