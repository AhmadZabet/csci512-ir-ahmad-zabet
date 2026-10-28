"""Hand-checked examples for the tokenization policy."""

import unittest

from src.text_ops import tokenize


class TokenizeTests(unittest.TestCase):
    def test_lecture_example(self):
        text = (
            "In 1962, Cleverdon's high-speed tests at Mach 2.5 "
            "cost $2,000 (U.S.A.)."
        )

        self.assertEqual(
            tokenize(text),
            [
                "in", "1962", "cleverdon", "high", "speed", "tests",
                "at", "mach", "2.5", "cost", "2000", "usa",
            ],
        )

    def test_lowercase(self):
        self.assertEqual(
            tokenize("Wing WING wing"),
            ["wing", "wing", "wing"],
        )

    def test_hyphens(self):
        self.assertEqual(
            tokenize("high-speed state-of-the-art"),
            ["high", "speed", "state", "of", "the", "art"],
        )

    def test_apostrophes(self):
        self.assertEqual(
            tokenize("Cleverdon's don't O'Neill patients'"),
            ["cleverdon", "dont", "oneill", "patients"],
        )

    def test_curly_apostrophes(self):
        self.assertEqual(
            tokenize("Cleverdon\u2019s don\u2019t O\u2018Neill"),
            ["cleverdon", "dont", "oneill"],
        )

    def test_acronyms(self):
        self.assertEqual(
            tokenize("U.S.A. U.S.A USA U.K. Dr. Smith."),
            ["usa", "usa", "usa", "uk", "dr", "smith"],
        )

    def test_numbers(self):
        self.assertEqual(
            tokenize("1962 2.5 $2,000 1,000,000 2,000.50 -3.5 25%"),
            ["1962", "2.5", "2000", "1000000", "2000.50", "3.5", "25"],
        )

    def test_alphanumeric_terms(self):
        self.assertEqual(
            tokenize("B52 3D H2O"),
            ["b52", "3d", "h2o"],
        )

    def test_punctuation_and_whitespace(self):
        self.assertEqual(
            tokenize("heat,transfer;flow/wing\npressure\t(lift)"),
            ["heat", "transfer", "flow", "wing", "pressure", "lift"],
        )

    def test_preserves_order_repeats_and_stopwords(self):
        self.assertEqual(
            tokenize("The flow and the flow"),
            ["the", "flow", "and", "the", "flow"],
        )

    def test_empty_input(self):
        for text in ("", " \n\t", "... / --- !!!"):
            with self.subTest(text=text):
                self.assertEqual(tokenize(text), [])


if __name__ == "__main__":
    unittest.main()