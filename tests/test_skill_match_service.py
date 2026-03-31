import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services import skill_match_service as service


class SkillMatchServiceTests(unittest.TestCase):
    def setUp(self):
        service.get_model.cache_clear()
        service.get_skill_embeddings.cache_clear()
        service._skill_embedding_index.cache_clear()
        service._get_openai_client.cache_clear()

    def test_strong_match_candidate_evaluation(self):
        cv_text = (
            "Experienced Python backend engineer building FastAPI services with "
            "Docker and Kubernetes in production."
        )
        jd_text = (
            "Looking for a Python engineer with FastAPI, Docker, and Kubernetes experience."
        )

        result = service.evaluate_candidate(cv_text, jd_text)

        self.assertGreaterEqual(result["score"], 80.0)
        self.assertEqual([], result["missing_skills"])
        self.assertIn("Python", result["matched_skills"])
        self.assertIn("strong match", result["explanation"].lower())

    def test_weak_match_candidate_evaluation(self):
        cv_text = "HR coordinator focused on payroll, employee onboarding, and scheduling."
        jd_text = "Need a TensorFlow, Docker, Kubernetes, and Python engineer."

        result = service.evaluate_candidate(cv_text, jd_text)

        self.assertLess(result["score"], 50.0)
        self.assertTrue(result["missing_skills"])
        self.assertIn("weak match", result["explanation"].lower())

    def test_empty_job_description(self):
        result = service.evaluate_candidate("Python engineer with FastAPI.", "")

        self.assertEqual(0.0, result["score"])
        self.assertEqual([], result["matched_skills"])
        self.assertEqual([], result["missing_skills"])
        self.assertIn("job description", result["recommendations"][0].lower())

    def test_exact_skill_normalization_matches_original_skill_name(self):
        result = service.evaluate_candidate(
            "Python developer",
            "Python developer",
        )

        self.assertIn("Python", result["matched_skills"])
        self.assertEqual([], result["missing_skills"])

    def test_missing_semantic_dependency_falls_back_without_crashing(self):
        cv_text = "Python FastAPI Docker Kubernetes engineer."
        jd_text = "Python FastAPI Docker Kubernetes engineer."

        with patch.object(service, "get_model", return_value=None):
            service.get_skill_embeddings.cache_clear()
            service._skill_embedding_index.cache_clear()

            semantic_result = service.match_skills_semantic(
                cv_text,
                ["Python", "FastAPI", "Docker", "Kubernetes"],
            )
            evaluation = service.evaluate_candidate(cv_text, jd_text)

        self.assertEqual([], semantic_result["skills"])
        self.assertGreaterEqual(evaluation["score"], 80.0)
        self.assertEqual([], evaluation["missing_skills"])


if __name__ == "__main__":
    unittest.main()
