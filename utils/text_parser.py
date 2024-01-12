"""Common text parser functions for the plugin."""


# Function creates meta information for the post
def create_meta_information(category):
    """Create meta information for the post."""
    meta_information = {
        "protocol": "",
        "photograph": "",
        "title": category,
        "author": "",
        "category": category,
    }
    return meta_information


# Function returns all the text from the given PDF page
def get_raw_text(page):
    """Get the raw text from the PDF page."""
    # get raw text from page
    raw_text = page.get_text()
    return raw_text
