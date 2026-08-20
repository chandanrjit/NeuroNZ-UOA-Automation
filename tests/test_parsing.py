import unittest

from neuronz_automation.parsing import extract_doi, extract_pmid, parse_extra


class ParsingTests(unittest.TestCase):
    def test_parse_extra_reads_neuronz_fields(self):
        parsed = parse_extra(
            """NeuroNZ Record ID: NZNEURO-079
Source category: International data system
Available in IDI: No
All source links: https://example.test/source
"""
        )

        self.assertEqual(parsed["NeuroNZ Record ID"], "NZNEURO-079")
        self.assertEqual(parsed["Source category"], "International data system")
        self.assertEqual(parsed["Available in IDI"], "No")

    def test_extract_doi_from_url_text(self):
        self.assertEqual(
            extract_doi("https://doi.org/10.1161/STROKEAHA.116.013947"),
            "10.1161/STROKEAHA.116.013947",
        )

    def test_extract_pmid_from_pubmed_url(self):
        self.assertEqual(extract_pmid("https://pubmed.ncbi.nlm.nih.gov/27470991/"), "27470991")


if __name__ == "__main__":
    unittest.main()
