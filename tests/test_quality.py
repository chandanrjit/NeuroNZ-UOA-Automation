import unittest

from neuronz_automation.quality import changed_record_rows, review_queue_rows, validation_rows


class QualityTests(unittest.TestCase):
    def test_validation_blocks_missing_required_public_fields(self):
        rows = validation_rows(
            [
                {
                    "record_id": "NZNEURO-001",
                    "title": "",
                    "primary_link": "",
                    "source_category": "Administrative",
                    "availability_access": "Public",
                }
            ]
        )

        blocker_fields = {row["field"] for row in rows if row["severity"] == "blocker"}
        self.assertEqual(blocker_fields, {"title", "primary_link"})

    def test_review_queue_includes_verification_pending(self):
        rows = validation_rows(
            [
                {
                    "record_id": "NZNEURO-002",
                    "title": "Record",
                    "primary_link": "https://example.test",
                    "source_category": "Registry",
                    "availability_access": "Verification pending",
                }
            ]
        )

        self.assertEqual(len(review_queue_rows(rows)), 4)

    def test_changed_record_rows_detects_changes(self):
        rows = changed_record_rows(
            [{"record_id": "NZNEURO-001", "title": "Old"}],
            [{"record_id": "NZNEURO-001", "title": "New"}],
        )

        self.assertEqual(rows[0]["change_status"], "changed")
        self.assertEqual(rows[0]["changed_fields"], "title")


if __name__ == "__main__":
    unittest.main()

