""" Test the extract_page_0.py file. """

from parsers.extract_page_0 import extract_color_code
from test_main import TestMain


class TestExtractPage0(TestMain):
    """Test the extract_page_0.py file."""

    def test_extract_color_code(self) -> None:
        """Test if the color code is extracted correctly."""
        hex_color_code = extract_color_code(self.test1)
        assert hex_color_code == "#e7534a"

        hex_color_code2 = extract_color_code(self.test2)
        assert hex_color_code2 == "#ffc44b"

        hex_color_code3 = extract_color_code(self.test3)
        assert hex_color_code3 == "#55b2d1"

        hex_color_code4 = extract_color_code(self.test4)
        assert hex_color_code4 == "#f4693c"

        hex_color_code5 = extract_color_code(self.test5)
        assert hex_color_code5 == "#ea405b"
