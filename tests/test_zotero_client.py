import unittest
from unittest.mock import patch

from neuronz_automation.run_phase2 import partition_items
from neuronz_automation.zotero_client import ZoteroClient


class GroupCollectionTests(unittest.TestCase):
    def test_group_path_and_pagination(self):
        client = ZoteroClient()
        with patch.object(ZoteroClient, "_get_json", side_effect=[[{"key": "A"}], []]) as get:
            self.assertEqual(client.fetch_collection_items("PA2ESN45", limit=1), [{"key": "A"}])
        self.assertEqual(get.call_args_list[0].args[0], "/groups/6643086/collections/PA2ESN45/items")
        self.assertEqual(get.call_args_list[1].args[1]["start"], 1)

    def test_descendants_deduplicated_and_excluded_branch_skipped(self):
        client = ZoteroClient()
        def get_all(path, limit=100):
            if path.endswith("/PA2ESN45/collections"):
                return [
                    {"key": "CHILD", "data": {"name": "02 Evidence Log"}},
                    {"key": "EXCLUDED", "data": {"name": "04 Excluded Sources"}},
                ]
            return []
        with patch.object(ZoteroClient, "_get_all", side_effect=get_all), patch.object(
            ZoteroClient, "fetch_collection_items", return_value=[{"key": "A"}]
        ) as fetch:
            self.assertEqual(client.fetch_collection_tree_items("PA2ESN45"), [{"key": "A"}])
        self.assertEqual([call.args[0] for call in fetch.call_args_list], ["PA2ESN45", "CHILD"])

    def test_evidence_reference_is_not_catalogue_and_unknown_is_validated(self):
        items = [
            {"data": {"extra": "NeuroNZ Evidence ID: E1\nNeuroNZ Record ID: R1"}},
            {"data": {"extra": "NeuroNZ Condition ID: C1"}},
            {"data": {"extra": "NeuroNZ Record ID: R2"}},
            {"data": {"title": "Missing ID"}},
            {"data": {"itemType": "attachment"}},
        ]
        buckets = partition_items(items)
        self.assertEqual(buckets["evidence"], items[:1])
        self.assertEqual(buckets["taxonomy"], items[1:2])
        self.assertEqual(buckets["catalogue"], items[2:4])
