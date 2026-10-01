import json
import unittest
from neuronz_automation.taxonomy import classify, condition_patch, audit_items
from neuronz_automation.dataset_updates import dataset_issue, dataset_item

TAXONOMY = [{"key": "STROKE", "data": {"title": "Stroke", "extra": "NeuroNZ Condition ID: NC-072"}},
            {"key": "TBI", "data": {"title": "Traumatic brain injury", "extra": "NeuroNZ Condition ID: NC-077"}}]


class TaxonomyTests(unittest.TestCase):
    def test_explicit_condition_and_nontraumatic_exclusion(self):
        self.assertEqual(classify("Stroke cohort", TAXONOMY)[0]["condition_id"], "NC-072")
        self.assertEqual(classify("Non-traumatic acute brain injury", TAXONOMY), [])
        self.assertEqual(classify("Stroke-like symptoms", TAXONOMY), [])
        self.assertEqual(classify("Non-traumatic brain injury", TAXONOMY), [])

    def test_patch_preserves_tags_and_curated_condition_ids(self):
        data = {"tags": [{"tag": "curated"}], "extra": "NeuroNZ Condition IDs: NC-077"}
        patch = condition_patch(data, classify("Stroke", TAXONOMY))
        self.assertEqual(patch, {})

    def test_audit_exposes_unknown_ids_and_missing_bibliography(self):
        item = {"key": "E", "data": {"itemType": "journalArticle", "extra": "NeuroNZ Evidence ID: E1\nNeuroNZ Condition IDs: BAD"}}
        gaps = audit_items([item], TAXONOMY)[0]["gaps"]
        self.assertIn("unknown_condition_id", gaps)
        self.assertIn("missing_publicationTitle", gaps)

    def test_dataset_requires_verified_public_resources_and_preserves_full_description(self):
        candidate = {"candidate_id": "data-govt-nz:1", "status": "candidate", "title": "Stroke dataset",
                     "summary": "New Zealand stroke data " + "x" * 1200, "source_organisation": "NZ agency",
                     "url": "https://catalogue.data.govt.nz/dataset/stroke",
                     "dataset_metadata": json.dumps({"private": False, "resources": ["https://example.org/data.csv"], "license": "CC BY"})}
        matches = classify(candidate["title"], TAXONOMY)
        self.assertEqual(dataset_issue(candidate, matches), "")
        item = dataset_item(candidate, "CAT", "NZNEURO-080", matches)
        self.assertEqual(item["abstractNote"], candidate["summary"])
        candidate["dataset_metadata"] = json.dumps({"private": True})
        self.assertIn("not verified", dataset_issue(candidate, matches))
