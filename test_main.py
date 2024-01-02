"""Tests main.py file for the FastAPI application."""

from test_setup import TestMain


class TestUtils(TestMain):
    """Test class to test all functions within utils.py file."""

    def test_read_main(self):
        """Test the main endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200

    def test_upload_files(self):
        """Test the upload endpoint."""
        with open(self.test1, "rb") as f:
            files = {"file": f}
            response = self.client.post("/upload", files=files)
            assert response.status_code == 200
            assert response.json() == {
                "message": "Uploaded 582_augustin_fertig_kontrolle.pdf and post empty"
            }

        with open(self.test2, "rb") as f:
            files = {"file": f}
            response = self.client.post("/upload", files=files)
            assert response.status_code == 200
            assert response.json() == {
                "message": "Uploaded 576_augustin_fertig_kontrolle.pdf and post empty"
            }

        with open(self.test3, "rb") as f:
            files = {"file": f}
            response = self.client.post("/upload", files=files)
            assert response.status_code == 200
            assert response.json() == {
                "message": "Uploaded 575_augustin_fertig_kontrolle.pdf and post empty"
            }

        with open(self.test4, "rb") as f:
            files = {"file": f}
            response = self.client.post("/upload", files=files)
            assert response.status_code == 200
            assert response.json() == {
                "message": "Uploaded 574_augustin_fertig_kontrolle.pdf and post empty"
            }

        with open(self.test5, "rb") as f:
            files = {"file": f}
            response = self.client.post("/upload", files=files)
            assert response.status_code == 200
            assert response.json() == {
                "message": "Uploaded 570_augustin_fertig_kontrolle.pdf and post empty"
            }
