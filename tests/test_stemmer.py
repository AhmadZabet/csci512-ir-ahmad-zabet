"""Tests for Porter's measure and conditions."""

import unittest

from src.stemmer import (
    consonants,
    measure,
    contains_vowel,
    ends_double_consonant,
    ends_cvc,
)


class PorterConditionTests(unittest.TestCase):

    def test_measure_examples(self):
        """Check the measure values from the lecture."""

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
        """Check that y changes classification with its context."""

        self.assertEqual(consonants("yes"), [True, False, True])
        self.assertEqual(consonants("by"), [True, False])
        self.assertEqual(consonants("toy"), [True, False, True])

    def test_contains_vowel(self):
        """Check the vowel condition on candidate stems."""

        self.assertTrue(contains_vowel("happ"))
        self.assertFalse(contains_vowel("sk"))
        self.assertFalse(contains_vowel(""))

    def test_double_consonant(self):
        """A repeated final vowel must not count as a double consonant."""

        self.assertTrue(ends_double_consonant("hopp"))
        self.assertTrue(ends_double_consonant("fall"))
        self.assertFalse(ends_double_consonant("see"))
        self.assertFalse(ends_double_consonant(""))

    def test_cvc(self):
        """Check CVC endings and excluded final letters."""

        self.assertTrue(ends_cvc("fil"))
        self.assertTrue(ends_cvc("hop"))

        for word in ("snow", "box", "toy", "fail", ""):
            with self.subTest(word=word):
                self.assertFalse(ends_cvc(word))


if __name__ == "__main__":
    unittest.main()