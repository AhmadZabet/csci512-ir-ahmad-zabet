"""Tests for original Porter rules and Harman's S-stemmer."""

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
    step4,
    step5a,
    step5b,
    porter_stem,
    s_stem,
)


class ExampleTests(unittest.TestCase):
    """Provide a reusable helper for testing word/result pairs."""

    def check_examples(self, function, examples):
        """Run each example as a separately identified subtest."""

        for word, expected in examples.items():
            with self.subTest(function=function.__name__, word=word):
                self.assertEqual(function(word), expected)


class PorterConditionTests(ExampleTests):
    """Check the conditions used by Porter suffix rules."""

    def test_measure_examples(self):
        """Check measure values from the lecture."""

        self.check_examples(measure, {
            "": 0,
            "by": 0,
            "flow": 1,
            "ivy": 1,
            "boundary": 2,
            "syzygy": 2,
            "aerodynamic": 5,
        })

    def test_contextual_y(self):
        """Check initial Y and Y following vowels/consonants."""

        self.check_examples(consonants, {
            "yes": [True, False, True],
            "by": [True, False],
            "toy": [True, False, True],
        })

    def test_contains_vowel(self):
        """Check vowel presence in candidate stems."""

        self.check_examples(contains_vowel, {
            "happ": True,
            "sk": False,
            "": False,
        })

    def test_double_consonant(self):
        """Repeated vowels must not count as double consonants."""

        self.check_examples(ends_double_consonant, {
            "hopp": True,
            "fall": True,
            "see": False,
            "": False,
        })

    def test_cvc(self):
        """Check CVC endings and final W/X/Y exclusions."""

        self.check_examples(ends_cvc, {
            "fil": True,
            "hop": True,
            "snow": False,
            "box": False,
            "toy": False,
            "fail": False,
            "": False,
        })


class PorterStep1Tests(ExampleTests):
    """Check individual Step 1 rules and their combined behavior."""

    def test_step1a(self):
        """Check plural rules and the protective SS rule."""

        self.check_examples(step1a, {
            "caresses": "caress",
            "ponies": "poni",
            "ties": "ti",
            "caress": "caress",
            "cats": "cat",
            "flows": "flow",
        })

    def test_step1b(self):
        """Check suffix conditions and cleanup branches."""

        self.check_examples(step1b, {
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
        })

    def test_step1c(self):
        """Check the vowel condition for final Y replacement."""

        self.check_examples(step1c, {
            "happy": "happi",
            "sky": "sky",
            "boy": "boi",
        })

    def test_complete_step1(self):
        """Check Steps 1a–1c in sequence."""

        self.check_examples(step1, {
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
        })


class PorterSteps2And3Tests(ExampleTests):
    """Check original Porter Steps 2 and 3."""

    def test_step2_rules(self):
        """Check every Step 2 replacement."""

        self.check_examples(step2, {
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
        })

    def test_step3_rules(self):
        """Check every Step 3 replacement."""

        self.check_examples(step3, {
            "triplicate": "triplic",
            "formative": "form",
            "formalize": "formal",
            "electriciti": "electric",
            "electrical": "electric",
            "hopeful": "hope",
            "goodness": "good",
        })

    def test_failed_longest_match_stops_the_step(self):
        """Do not try a shorter suffix after a failed longest match."""

        self.assertEqual(step2("rational"), "rational")

        rules = (
            ("tional", "tion"),
            ("ational", "ate"),
        )

        self.assertEqual(
            apply_measured_rules("rational", rules),
            "rational",
        )

    def test_measure_must_be_positive(self):
        """Reject replacements when the candidate stem is empty."""

        self.assertEqual(step2("ational"), "ational")
        self.assertEqual(step3("ness"), "ness")

    def test_original_abli_rule(self):
        """Keep original ABLI behavior without adding a BLI rule."""

        self.check_examples(step2, {
            "conformabli": "conformable",
            "possibly": "possibly",
            "possibli": "possibli",
        })

    def test_steps_in_sequence(self):
        """Check intermediate results after Steps 1–3."""

        examples = {
            "generalizations": "general",
            "hopefulness": "hope",
            "compressibility": "compressible",
        }

        for word, expected in examples.items():
            with self.subTest(word=word):
                result = step3(step2(step1(word)))
                self.assertEqual(result, expected)

    def test_unchanged_and_empty_words(self):
        """Pass through words without applicable suffixes."""

        for word in ("flow", "wing", ""):
            with self.subTest(word=word):
                self.assertEqual(step2(word), word)
                self.assertEqual(step3(word), word)


class PorterSteps4And5Tests(ExampleTests):
    """Check final suffix removal and cleanup."""

    def test_step4_rules(self):
        """Check every Step 4 suffix."""

        self.check_examples(step4, {
            "revival": "reviv",
            "allowance": "allow",
            "inference": "infer",
            "airliner": "airlin",
            "gyroscopic": "gyroscop",
            "adjustable": "adjust",
            "defensible": "defens",
            "irritant": "irrit",
            "replacement": "replac",
            "adjustment": "adjust",
            "dependent": "depend",
            "adoption": "adopt",
            "homologou": "homolog",
            "communism": "commun",
            "activate": "activ",
            "angulariti": "angular",
            "homologous": "homolog",
            "effective": "effect",
            "bowdlerize": "bowdler",
        })

    def test_step4_conditions(self):
        """Check measure, ION restrictions, and longest-match behavior."""

        self.check_examples(step4, {
            # The remaining stem does not end in S or T.
            "million": "million",

            # The candidate stem's measure is only 1.
            "fiction": "fiction",

            # EMENT matches first and leaves c with measure 0.
            "cement": "cement",
        })

    def test_step5a(self):
        """Check final E removal and the short-CVC exception."""

        self.check_examples(step5a, {
            "probate": "probat",
            "rate": "rate",
            "cease": "ceas",
            "be": "be",
            "": "",
        })

    def test_step5b(self):
        """Reduce LL only when the measure exceeds one."""

        self.check_examples(step5b, {
            "controll": "control",
            "roll": "roll",
            "fall": "fall",
            "hiss": "hiss",
            "": "",
        })

    def test_complete_porter(self):
        """Check complete stems, including required lecture examples."""

        self.check_examples(porter_stem, {
            "generalizations": "gener",
            "oscillators": "oscil",
            "relational": "relat",
            "conditional": "condit",
            "hopefulness": "hope",
            "compressibility": "compress",
            "experimental": "experiment",
            "experiments": "experi",
            "university": "univers",
            "universe": "univers",
            "news": "new",
            "agreed": "agre",
            "filing": "file",
            "sky": "sky",
            "": "",
        })


class SStemmerTests(ExampleTests):
    """Check the lighter S-stemmer and compare it with Porter."""

    def test_plural_examples(self):
        """Check plural changes and preserved US/SS endings."""

        self.check_examples(s_stem, {
            "ponies": "pony",
            "horses": "horse",
            "toes": "toe",
            "cats": "cat",
            "flows": "flow",
            "status": "status",
            "caress": "caress",
            "trees": "tree",
        })

    def test_ies_exceptions(self):
        """Excluded IES endings can qualify for a later rule."""

        # Artificial strings isolate the AIES/EIES exceptions.
        self.check_examples(s_stem, {
            "aies": "aie",
            "eies": "eie",
        })

    def test_es_exceptions(self):
        """Excluded ES endings can still qualify for final S removal."""

        self.check_examples(s_stem, {
            "algaes": "algae",
            "trees": "tree",
            "toes": "toe",
        })

    def test_unchanged_words(self):
        """Do not remove ING or derivational suffixes."""

        for word in ("flow", "flowing", "experimental", ""):
            with self.subTest(word=word):
                self.assertEqual(s_stem(word), word)

    def test_difference_from_porter(self):
        """Demonstrate differences between the two algorithms."""

        examples = (
            ("ponies", "pony", "poni"),
            ("horses", "horse", "hors"),
            ("flowing", "flowing", "flow"),
        )

        for word, light, porter in examples:
            with self.subTest(word=word):
                self.assertEqual(s_stem(word), light)
                self.assertEqual(porter_stem(word), porter)


if __name__ == "__main__":
    unittest.main()