"""Tests for Porter's conditions and Step 1.

Run from the repository root:
python -B -m unittest discover -s tests -p test_stemmer.py -v
"""

import unittest

from src.stemmer import (
    consonants,
    measure,
    contains_vowel,
    ends_double_consonant,
    ends_cvc,
    step1a,
    step1b,
    step1c,
    step1,
)


class PorterConditionTests(unittest.TestCase):
    """Check the conditions used by the suffix rules."""

    def test_measure_examples(self):
        """Check lecture examples for Porter's measure m."""

        examples = {
            "": 0,
            "by": 0,
            "flow": 1,
            "ivy": 1,
            "boundary": 2,
            "syzygy": 2,
            "aerodynamic": 5,
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(measure(word), expected)

    def test_contextual_y(self):
        """Check initial Y and Y after vowels and consonants."""

        self.assertEqual(
            consonants("yes"),
            [True, False, True],
        )

        self.assertEqual(
            consonants("by"),
            [True, False],
        )

        self.assertEqual(
            consonants("toy"),
            [True, False, True],
        )

    def test_contains_vowel(self):
        """Check whether candidate stems contain a Porter vowel."""

        self.assertTrue(contains_vowel("happ"))
        self.assertFalse(contains_vowel("sk"))
        self.assertFalse(contains_vowel(""))

    def test_double_consonant(self):
        """Repeated vowels must not count as double consonants."""

        self.assertTrue(ends_double_consonant("hopp"))
        self.assertTrue(ends_double_consonant("fall"))

        self.assertFalse(ends_double_consonant("see"))
        self.assertFalse(ends_double_consonant(""))

    def test_cvc(self):
        """Check CVC endings, including the W/X/Y exclusions."""

        self.assertTrue(ends_cvc("fil"))
        self.assertTrue(ends_cvc("hop"))

        for word in ("snow", "box", "toy", "fail", ""):
            with self.subTest(word=word):
                self.assertFalse(ends_cvc(word))


class PorterStep1Tests(unittest.TestCase):
    """Check individual Step 1 rules and their combined behavior."""

    def test_step1a(self):
        """Check plural suffixes and the protective SS rule."""

        examples = {
            "caresses": "caress",
            "ponies": "poni",
            "ties": "ti",
            "caress": "caress",
            "cats": "cat",
            "flows": "flow",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(step1a(word), expected)

    def test_step1b(self):
        """Check suffix conditions and all cleanup branches."""

        examples = {
            "agreed": "agree",
            "feed": "feed",
            "plastered": "plaster",
            "bled": "bled",
            "motoring": "motor",
            "sing": "sing",
            "conflated": "conflate",
            "troubled": "trouble",
            "sized": "size",
            "hopping": "hop",
            "tanned": "tan",
            "falling": "fall",
            "hissing": "hiss",
            "fizzed": "fizz",
            "filing": "file",
            "failing": "fail",
            "snowing": "snow",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(step1b(word), expected)

    def test_step1c(self):
        """Check that final Y changes only when its stem has a vowel."""

        examples = {
            "happy": "happi",
            "sky": "sky",
            "boy": "boi",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(step1c(word), expected)

    def test_complete_step1(self):
        """Check Steps 1a–1c together, in the required order."""

        examples = {
            "ponies": "poni",
            "caresses": "caress",
            "agreed": "agree",
            "motoring": "motor",
            "hopping": "hop",
            "filing": "file",
            "falling": "fall",
            "conflated": "conflate",
            "sized": "size",
            "happy": "happi",
            "sky": "sky",
            "flows": "flow",
            "": "",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(step1(word), expected)


if __name__ == "__main__":
    unittest.main()