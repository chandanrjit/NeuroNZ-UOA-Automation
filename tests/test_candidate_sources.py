import unittest
import json

from neuronz_automation.candidate_sources import candidate_error, pubmed_metadata


class CandidateSourceTests(unittest.TestCase):
    def test_pubmed_bibliography_preserves_authors_dates_and_page_ranges(self):
        xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article>
        <ArticleTitle>A <i>stroke</i> study</ArticleTitle><Journal><Title>Journal of Neurology</Title>
        <ISOAbbreviation>J Neurol</ISOAbbreviation><ISSN>1234-5678</ISSN><JournalIssue><Volume>8</Volume>
        <Issue>2</Issue><PubDate><Year>2026</Year><Month>Sep</Month><Day>4</Day></PubDate></JournalIssue></Journal>
        <Pagination><StartPage>247</StartPage><EndPage>252</EndPage></Pagination>
        <AuthorList><Author><ForeName>Ana</ForeName><LastName>Smith</LastName></Author>
        <Author><CollectiveName>NZ Study Group</CollectiveName></Author></AuthorList><Language>eng</Language>
        </Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""
        record = pubmed_metadata(xml)["123"]
        fields = json.loads(record["bibliography"])
        self.assertEqual(record["title"], "A stroke study")
        self.assertEqual(fields["publicationTitle"], "Journal of Neurology")
        self.assertEqual(fields["date"], "2026-Sep-4")
        self.assertEqual(fields["pages"], "247-252")
        self.assertEqual(fields["creators"][1]["name"], "NZ Study Group")

    def test_candidate_error_uses_reviewable_shape(self):
        row = candidate_error("pubmed", "failed")

        self.assertEqual(row["source_id"], "pubmed")
        self.assertEqual(row["candidate_type"], "source_error")
        self.assertEqual(row["status"], "error")
        self.assertEqual(row["error_message"], "failed")


if __name__ == "__main__":
    unittest.main()
