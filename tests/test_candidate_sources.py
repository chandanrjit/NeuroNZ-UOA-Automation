import unittest

from neuronz_automation.candidate_sources import candidate_error


class CandidateSourceTests(unittest.TestCase):
    def test_candidate_error_uses_reviewable_shape(self):
        row = candidate_error("pubmed", "failed")

        self.assertEqual(row["source_id"], "pubmed")
        self.assertEqual(row["candidate_type"], "source_error")
        self.assertEqual(row["status"], "error")
        self.assertEqual(row["error_message"], "failed")


if __name__ == "__main__":
    unittest.main()

