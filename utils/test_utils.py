""" Test the utils.py file. """

from test_main import TestMain
from utils.utils import PluginUtility


class TestUtils(TestMain):
    """Test class to test all functions within utils.py file."""

    def test_split_pdf_a3_to_a4(self) -> None:
        """Test if the color code is extracted correctly."""
        plugin_utitlity = PluginUtility()

        index = plugin_utitlity.split_pdf_a3_to_a4(self.test1, self.save1)
        assert index == 14

        index2 = plugin_utitlity.split_pdf_a3_to_a4(self.test2, self.save2)
        assert index2 == 27

        index3 = plugin_utitlity.split_pdf_a3_to_a4(self.test3, self.save3)
        assert index3 == 14

        index4 = plugin_utitlity.split_pdf_a3_to_a4(self.test4, self.save4)
        assert index4 == 14

        index5 = plugin_utitlity.split_pdf_a3_to_a4(self.test5, self.save5)
        assert index5 == 16

    def test_global_vars(self) -> None:
        """Test if the global variables are set correctly."""
        print("qwwqqweq", self.test_data_path)
        assert (
            self.test_data_path
            == "/home/funny/Documents/Projects/230701-Parsing-Tool/augustin-plugin/test_data/"
        )
        assert self.global_url == "http://localhost:10014/wp-json/wp/v2/"
