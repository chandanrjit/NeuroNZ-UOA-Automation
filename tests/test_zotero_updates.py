import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from neuronz_automation.zotero_updates import relevance_issue, update_candidates


def candidate():
    return {"candidate_id": "pubmed:12345", "source_id": "pubmed", "status": "candidate",
            "title": "Stroke outcomes in New Zealand", "summary": "A New Zealand cohort study of stroke outcomes.",
            "pmid": "12345", "url": "https://pubmed.ncbi.nlm.nih.gov/12345/", "doi": "10.1234/example"}


class ZoteroUpdateTests(unittest.TestCase):
    def client(self):
        client = Mock()
        client.fetch_child_collections.return_value = [{"key": "KFGR6AVK", "data": {"name": "02 Evidence Log"}}]
        client.fetch_library_items.return_value = [{"data": {"extra": "NeuroNZ Evidence ID: E102"}}]
        client.create_item.return_value = {"key": "NEWKEY"}
        client.fetch_item.return_value = {"key": "NEWKEY", "version": 2, "data": {
            "title": "Stroke outcomes in New Zealand", "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            "collections": ["KFGR6AVK"], "extra": "NeuroNZ Evidence ID: E103",
            "dateAdded": "2026-10-02T00:00:00Z", "dateModified": "2026-10-02T00:00:00Z"}}
        return client

    def test_verified_creation_and_duplicate_in_same_batch(self):
        client = self.client()
        with tempfile.TemporaryDirectory() as directory:
            rows = update_candidates(client, [candidate(), candidate()], Path(directory))
        self.assertEqual([r["status"] for r in rows], ["created_verified", "duplicate"])
        self.assertEqual(rows[0]["evidence_id"], "E103")
        self.assertEqual(rows[0]["date_modified"], "2026-10-02T00:00:00Z")
        client.create_item.assert_called_once()

    def test_existing_doi_skips_write(self):
        client = self.client()
        client.fetch_library_items.return_value = [{"data": {"DOI": "10.1234/example"}}]
        with tempfile.TemporaryDirectory() as directory:
            rows = update_candidates(client, [candidate()], Path(directory))
        self.assertEqual(rows[0]["status"], "duplicate")
        client.create_item.assert_not_called()

    def test_readback_failure_keeps_key_receipt(self):
        client = self.client()
        client.fetch_item.side_effect = RuntimeError("Read failed")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                update_candidates(client, [candidate()], Path(directory))
            receipt = (Path(directory) / "zotero_update_manifest.json").read_text()
            self.assertIn("created_unverified", receipt)
            self.assertIn("NEWKEY", receipt)

    def test_irrelevant_and_animal_matches_require_review(self):
        row = candidate()
        row["summary"] = "A study of New Zealand White rabbits with stroke."
        self.assertIn("Animal breed", relevance_issue(row))
        row = candidate()
        row["title"] = "Kidney transplantation"
        self.assertIn("requires review", relevance_issue(row))
