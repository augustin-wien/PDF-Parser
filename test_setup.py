"""Sets up the test environment."""
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
        cls.test_data_path = os.environ.get("TEST_DATA_PATH")
        print(cls.test_data_path)
        cls.global_save_path = os.environ.get("SAVE_PATH")
        cls.global_url = os.environ.get("WORDPRESS_URL")
        cls.debug = os.environ.get("DEBUG")
        cls.client = TestClient(app)

        # Create path to test files
        cls.test1 = cls.test_data_path + "582_augustin_fertig_kontrolle.pdf"
        cls.test2 = cls.test_data_path + "576_augustin_fertig_kontrolle.pdf"
        cls.test3 = cls.test_data_path + "575_augustin_fertig_kontrolle.pdf"
        cls.test4 = cls.test_data_path + "574_augustin_fertig_kontrolle.pdf"
        cls.test5 = cls.test_data_path + "570_augustin_fertig_kontrolle.pdf"

        # Create saving paths
        cls.save1 = cls.global_save_path + "582_augustin_fertig_kontrolle/"
        cls.save2 = cls.global_save_path + "576_augustin_fertig_kontrolle/"
        cls.save3 = cls.global_save_path + "575_augustin_fertig_kontrolle/"
        cls.save4 = cls.global_save_path + "574_augustin_fertig_kontrolle/"
        cls.save5 = cls.global_save_path + "570_augustin_fertig_kontrolle/"
