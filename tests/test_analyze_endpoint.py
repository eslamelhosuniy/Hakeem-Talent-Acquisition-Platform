import sys
import unittest
from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import main


class AnalyzeEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_analyze_json_input(self):
        response = self.client.post(
            "/analyze",
            json={
                "cv_text": "Experienced Python backend engineer building FastAPI services with Docker and Kubernetes.",
                "job_description": "Looking for a Python engineer with FastAPI, Docker, and Kubernetes experience.",
            },
        )

        body = response.json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("analysis_success", body["signal"])
        self.assertIn("parsed_cv", body["data"])
        self.assertIn("skills", body["data"])
        self.assertEqual([], body["data"]["skills"]["missing"])

    def test_analyze_docx_upload(self):
        document = Document()
        document.add_paragraph(
            "Python backend engineer with FastAPI, Docker, and Kubernetes experience."
        )
        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)

        response = self.client.post(
            "/analyze",
            data={
                "job_description": "Looking for a Python engineer with FastAPI, Docker, and Kubernetes experience."
            },
            files={
                "file": (
                    "resume.docx",
                    buffer.getvalue(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        body = response.json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("analysis_success", body["signal"])
        self.assertTrue(body["data"]["skills"]["extracted"])

    def test_missing_job_description_returns_validation_error(self):
        response = self.client.post(
            "/analyze",
            json={"cv_text": "Python backend engineer with FastAPI."},
        )

        body = response.json()
        self.assertEqual(422, response.status_code)
        self.assertEqual("analysis_error", body["signal"])
        self.assertIn("job_description", body["error"])

    def test_unsupported_file_type_returns_error(self):
        response = self.client.post(
            "/analyze",
            data={"job_description": "Python engineer"},
            files={"file": ("resume.txt", b"plain text resume", "text/plain")},
        )

        body = response.json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("analysis_error", body["signal"])
        self.assertIn("Unsupported file type", body["error"])


if __name__ == "__main__":
    unittest.main()
