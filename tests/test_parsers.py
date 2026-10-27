"""Parser examples and document-count checks.

Run from the repository root.
Collection tests require the downloaded files under data/.
LISA uses the instructor's corrected count of 5,999 documents.
"""

from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from src.parsers import (
    parse_medline,
    parse_cran,
    parse_cisi,
    parse_npl,
    parse_lisa,
)


class MedlineParserTests(unittest.TestCase):
    def test_extracts_w_and_saves_last_document(self):
        # Nonconsecutive IDs and no newline after the final document.
        sample = (
            ".I 7\n.T\nIgnored title\n"
            ".W\n  First   line.\nSecond\tline!\n"
            ".A\nIgnored author\n"
            ".I 42\n.W\nLast document."
        )

        with patch.object(Path, "open", return_value=StringIO(sample)):
            documents = parse_medline("example.all")

        self.assertEqual(
            documents,
            {
                7: "First line. Second line!",
                42: "Last document.",
            },
        )

    @unittest.skipUnless(
        Path("data/med/MED.ALL").is_file(),
        "Download MED.ALL first",
    )
    def test_medline_document_count(self):
        documents = parse_medline("data/med/MED.ALL")

        self.assertEqual(len(documents), 1033)
        self.assertEqual(set(documents), set(range(1, 1034)))
        self.assertTrue(all(documents.values()))


class OtherCollectionTests(unittest.TestCase):
    def test_smart_title_and_text(self):
        sample = (
            ".I 7\n.T\nTitle\n"
            ".A\nIgnored author\n"
            ".W\nBody\n"
            ".X\nIgnored references\n"
        )

        for parser in (parse_cran, parse_cisi):
            with self.subTest(parser=parser.__name__):
                with patch.object(
                    Path, "open", return_value=StringIO(sample)
                ):
                    documents = parser("example.all")

                self.assertEqual(documents, {7: "Title Body"})

    def test_npl_boundaries(self):
        # A numeric line inside a document remains part of its text.
        sample = "7\nFirst line\n123\n /\n9\nLast line\n/"

        with patch.object(Path, "open", return_value=StringIO(sample)):
            documents = parse_npl("example")

        self.assertEqual(
            documents,
            {
                7: "First line 123",
                9: "Last line",
            },
        )

    def test_collection_counts(self):
        cases = [
            (
                parse_cran,
                "data/cran/cran.all.1400",
                1400,
                {471, 995},
            ),
            (
                parse_cisi,
                "data/cisi/CISI.ALL",
                1460,
                set(),
            ),
            (
                parse_npl,
                "data/npl/doc-text",
                11429,
                set(),
            ),
        ]

        for parser, path, expected, expected_empty in cases:
            with self.subTest(collection=parser.__name__):
                documents = parser(path)

                self.assertEqual(len(documents), expected)
                self.assertEqual(
                    set(documents),
                    set(range(1, expected + 1)),
                )

                # CRAN records 471 and 995 are empty in the raw archive.
                empty_ids = {
                    doc_id
                    for doc_id, text in documents.items()
                    if not text
                }

                self.assertEqual(empty_ids, expected_empty)

    def test_lisa_document_count(self):
        # Instructor's corrected count for the supplied LISA collection.
        documents = parse_lisa("data/lisa")

        self.assertEqual(len(documents), 5999)
        self.assertTrue(all(documents.values()))

        # Preserve original IDs, including the archive's gaps.
        expected_ids = set(range(1, 6005)) - {
            1993, 1994, 1995, 1996, 1997
        }

        self.assertEqual(set(documents), expected_ids)


if __name__ == "__main__":
    unittest.main()