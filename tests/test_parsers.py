from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from src.parsers import parse_medline


class MedlineParserTests(unittest.TestCase):
    def test_extracts_w_and_saves_last_document(self):
        sample = (
            ".I 7\n.T\nIgnored title\n"
            ".W\n  First   line.\nSecond\tline!\n"
            ".A\nIgnored author\n"
            ".I 42\n.W\nLast document."
        )

        with patch.object(Path, "open", return_value=StringIO(sample)):
            documents = parse_medline("example.all")

        self.assertEqual(documents, {
            7: "First line. Second line!",
            42: "Last document.",
        })

    @unittest.skipUnless(
        Path("data/med/MED.ALL").is_file(),
        "Download MED.ALL first",
    )
    def test_medline_document_count(self):
        documents = parse_medline("data/med/MED.ALL")

        self.assertEqual(len(documents), 1033)
        self.assertEqual(set(documents), set(range(1, 1034)))
        self.assertTrue(all(documents.values()))


if __name__ == "__main__":
    unittest.main()