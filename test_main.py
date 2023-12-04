"""Main testing file for the FastAPI application."""

import os

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from main import app


class TestMain:
    """Test the main.py file and load global variables from .env file."""

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """

        load_dotenv()
        cls.global_path = os.environ.get("AUGUSTIN_PLUGIN_PATH")
        cls.global_url = os.environ.get("AUGUSTIN_PLUGIN_URL")
        cls.debug = os.environ.get("DEBUG")
        cls.client = TestClient(app)
        cls.test1 = cls.global_path + "582_augustin_fertig_kontrolle.pdf"
        cls.test2 = cls.global_path + "576_augustin_fertig_kontrolle.pdf"
        cls.test3 = cls.global_path + "575_augustin_fertig_kontrolle.pdf"
        cls.test4 = cls.global_path + "574_augustin_fertig_kontrolle.pdf"
        cls.test5 = cls.global_path + "570_augustin_fertig_kontrolle.pdf"

    def test_global_vars(self) -> None:
        """Test if the global variables are set correctly."""
        assert (
            self.global_path
            == "/home/funny/Documents/Projects/230701-Parsing-Tool/augustin-plugin/sample_data/"
        )
        assert self.global_url == "http://localhost:10014/wp-json/wp/v2/"

    # TODO test uploading a PDF file
    # Source: https://fastapi.tiangolo.com/tutorial/testing/

    # def test_read_main(self):
    #     response = self.client.get("/")
    #     assert response.status_code == 200
    #     assert response.json() == {"msg": "Hello World"}
