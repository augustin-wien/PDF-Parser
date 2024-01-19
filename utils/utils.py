"""Common utility functions for the plugin."""
import os

import fitz
from dotenv import load_dotenv
from utils.requests import upload_image


class PluginUtility:
    """Class for common utility functions for the plugin."""

    def __init__(self):
        load_dotenv()
        self.global_save_path = os.environ.get("SAVE_PATH")
        self.global_url = os.environ.get("WORDPRESS_URL")
        self.debug = os.environ.get("DEBUG")

        # Create a new PDF document for the output
        self.output_document = fitz.open()

    def download_image(self, page, doc, src):
        # Function code remains the same, but use self.global_path, self.debug, etc.
        # Replace global variables with self.<variable_name>
        """Download the image from the PDF file."""
        # Get image from PDF
        img_list = page.get_images(full=True)

        # iterate through image list to get single xref with positive values
        for img in img_list:
            i = 0
            rect = page.get_image_bbox(img)
            if rect[0] > 0 and rect[1] > 0 and rect[2] > 0 and rect[3] > 0:
                xref = img[0]  # get specific xref we want
                i += 1

        if i > 1:
            print("Warning: More than one image found on page 3")
        elif i == 1:
            image = doc.extract_image(xref)
        else:
            print("Warning: No image found on page 3")

        # write extracted image to file
        image_title = src.name.split(".")[0] + "_image_" + str(xref)
        image_path = os.path.join(
            self.global_save_path,
            image_title + "." + image["ext"],
        )
        with open(
            (image_path),
            "wb",
        ) as imgout:
            imgout.write(image["image"])
            imgout.close()

        image_id = upload_image(image_path, image_title)

        return image_id

    def get_size(self, filename):
        """Get the size of the image."""

        st = os.stat(filename)

        return st.st_size

    def save_pdf_a3_to_pdf_a4(self, path_to_file, path_to_new_directory):
        """Split the PDF file into single pages."""
        pdf_document = fitz.open(path_to_file)

        # Iterate through each page in the input PDF
        for spage in pdf_document:  # for each page in input
            if spage.rect.width < spage.rect.height:
                self.output_document.insert_pdf(
                    pdf_document, from_page=spage.number, to_page=spage.number
                )
                continue

            r = spage.rect  # input page rectangle
            d = fitz.Rect(
                spage.cropbox_position,  # CropBox displacement if not
                spage.cropbox_position,
            )  # starting at (0, 0)
            r1 = r  # top left rect
            r1.x1 /= 2  # half width
            r2 = r1 + (r1.width, 0, r1.width, 0)  # top right rect
            rect_list = [r1, r2]  # put them in a list

            for rx in rect_list:  # run thru rect list
                rx += d  # add the CropBox displacement
                page = self.output_document.new_page(
                    -1,  # new output page with rx dimensions
                    width=rx.width,
                    height=rx.height,
                )
                page.show_pdf_page(
                    page.rect,  # fill all new page with the imageb
                    pdf_document,  # input document
                    spage.number,  # input page number
                    clip=rx,  # which part to use of input page
                )
                #  Here we will convert the pdf to an image and check the size
                pix = page.get_pixmap()  # render page to an image
                name_png = f"{path_to_new_directory}page-{page.number}.png"  # _{random.randint(1,100)}
                pix.save(name_png)  # store image as a PNG
                imgsize = self.get_size(name_png)
                if not self.debug:
                    os.remove(name_png)
                if imgsize < 1300:
                    #  A6 blank page size approximately 1209 Yours may be different, check first
                    self.output_document.delete_page(pno=-1)
                    break
        # Save the output PDF
        self.output_document.save(path_to_file)
        self.output_document.close()

    def split_pdf_to_single_pdfs(self, save_path_for_pdf, path_to_save_files):
        # Function code remains the same, but use self.debug, self.global_path, etc.
        # Replace global variables with self.<variable_name>
        """Split the PDF file into single pages."""
        src = fitz.open(save_path_for_pdf)

        index = 0
        # Iterate through each page in the input PDF
        for index, _ in enumerate(src):
            self.output_document = fitz.open()
            self.output_document.insert_pdf(src, from_page=index, to_page=index)
            self.output_document.save(f"{path_to_save_files}page-{index}.pdf")

        return index

    def identify_category(self, page, i, path_to_new_directory):
        # Function code remains the same
        """Identify the category of the page."""
        rect = fitz.Rect(60, 30, 200, 60)
        if i % 2 == 0:
            rect = fitz.Rect(400, 30, 580, 60)

        text_in_rect = ""
        text_in_rect = self._check_for_word_in_rect(
            text_in_rect, page, rect, path_to_new_directory
        )

        # if no text was found in the rect, try to find the category on the side
        if text_in_rect == "":
            rect = fitz.Rect(10, 55, 80, 450)
            if i % 2 == 0:
                rect = fitz.Rect(450, 55, 580, 350)
            text_in_rect = self._check_for_word_in_rect(
                text_in_rect, page, rect, path_to_new_directory, True
            )

        # Last check if no text was found
        if text_in_rect == "":
            # probably full site advertisement
            text_in_rect = "Keine Kategorie gefunden"

        # Convert to downcase
        text_in_rect = text_in_rect.lower()

        # First page has a different structure
        if "editorial" in text_in_rect:
            text_in_rect = "editorial"

        return text_in_rect

    def _check_for_word_in_rect(
        self, text_in_rect, page, rect, path_to_new_directory, side_check=False
    ) -> str:
        """Check if a word is in the rect."""
        left, top, right, bottom = rect

        # Debug images for each page and category
        if self.debug:
            pix = page.get_pixmap(
                clip=(
                    left,
                    top,
                    right,
                    bottom,
                )
            )
            pix = page.get_pixmap(clip=(left, top, right, bottom))

            if side_check:
                pix.save(f"{path_to_new_directory}page-{page.number}-category_side.png")
            else:
                pix.save(f"{path_to_new_directory}page-{page.number}-category.png")

        for word in page.get_text("words"):
            x0, y0, x1, y1, text = word[:5]
            if (
                left <= x0 <= right
                and top <= y0 <= bottom
                and left <= x1 <= right
                and top <= y1 <= bottom
            ):
                text_in_rect += text + " "

        text_in_rect = text_in_rect.strip()

        return text_in_rect

    def upload_file(self, file):
        """Upload the file to the server."""

        # Create a new directory for each uploaded file
        path_to_new_directory = os.path.join(
            self.global_save_path, file.filename.split(".")[0]
        )

        # Catch error if directory already exists
        try:
            os.mkdir(path_to_new_directory)
        except OSError as error:
            print(error)

        # Save the uploaded file into the new directory
        save_path_for_pdf = os.path.join(path_to_new_directory, file.filename)
        with open(save_path_for_pdf, "wb") as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)

        # Add a slash to the end of the path
        path_to_new_directory = path_to_new_directory + "/"

        return save_path_for_pdf, path_to_new_directory
