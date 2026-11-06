"""Tests for Porter's conditions and Steps 1–3.

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
    apply_measured_rules,
    step2,
    step3,
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
        """Check CVC endings and the W/X/Y exclusions."""

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
        """Check Steps 1a–1c together in the required order."""

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


class PorterSteps2And3Tests(unittest.TestCase):
    """Check original Porter Steps 2 and 3."""

    def test_step2_rules(self):
        """Check every Step 2 replacement."""

        examples = {
            "relational": "relate",
            "conditional": "condition",
            "valenci": "valence",
            "hesitanci": "hesitance",
            "digitizer": "digitize",
            "conformabli": "conformable",
            "radicalli": "radical",
            "differentli": "different",
            "vileli": "vile",
            "analogousli": "analogous",
            "vietnamization": "vietnamize",
            "predication": "predicate",
            "operator": "operate",
            "feudalism": "feudal",
            "decisiveness": "decisive",
            "hopefulness": "hopeful",
            "callousness": "callous",
            "formaliti": "formal",
            "sensitiviti": "sensitive",
            "sensibiliti": "sensible",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(step2(word), expected)

    def test_step3_rules(self):
        """Check every Step 3 replacement."""

        examples = {
            "triplicate": "triplic",
            "formative": "form",
            "formalize": "formal",
            "electriciti": "electric",
            "electrical": "electric",
            "hopeful": "hope",
            "goodness": "good",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                self.assertEqual(step3(word), expected)

    def test_failed_longest_match_stops_the_step(self):
        """Do not try a shorter suffix after the longest match fails."""

        # ATIONAL leaves r, whose measure is zero.
        self.assertEqual(step2("rational"), "rational")

        # Even if rules arrive in this order, ATIONAL must be tried first.
        rules = (
            ("tional", "tion"),
            ("ational", "ate"),
        )

        self.assertEqual(
            apply_measured_rules("rational", rules),
            "rational",
        )

    def test_measure_must_be_positive(self):
        """A suffix with an empty candidate stem must remain unchanged."""

        self.assertEqual(step2("ational"), "ational")
        self.assertEqual(step3("ness"), "ness")

    def test_original_abli_rule(self):
        """Keep original ABLI behavior without adding a BLI rule."""

        self.assertEqual(step2("conformabli"), "conformable")
        self.assertEqual(step2("possibly"), "possibly")
        self.assertEqual(step2("possibli"), "possibli")

    def test_steps_in_sequence(self):
        """Check intermediate outputs after Steps 1, 2, and 3."""

        examples = {
            "generalizations": "general",
            "hopefulness": "hope",
            "compressibility": "compressible",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                result = step1(word)
                result = step2(result)
                result = step3(result)

                self.assertEqual(result, expected)

    def test_unchanged_and_empty_words(self):
        """Pass through words without applicable suffixes."""

        for word in ("flow", "wing", ""):
            with self.subTest(word=word):
                self.assertEqual(step2(word), word)
                self.assertEqual(step3(word), word)


if __name__ == "__main__":
    unittest.main()