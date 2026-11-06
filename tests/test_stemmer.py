"""Tests for Porter, the S-stemmer, caching, and NLTK agreement.

NLTK is used only here as a reference, not in the processing pipeline.
The whole-vocabulary check requires completed Phase 2 outputs.
"""

from collections import Counter
import csv
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

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
    stem_collection,
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
    """Check Step 1 rules and their combined behavior."""

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
            "million": "million",
            "fiction": "fiction",
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
        """Check complete stems and required lecture examples."""

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

        self.check_examples(s_stem, {
            "aies": "aie",
            "eies": "eie",
        })

    def test_es_exceptions(self):
        """Excluded ES endings can qualify for final S removal."""

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
        """Demonstrate differences between the algorithms."""

        examples = (
            ("ponies", "pony", "poni"),
            ("horses", "horse", "hors"),
            ("flowing", "flowing", "flow"),
        )

        for word, light, porter in examples:
            with self.subTest(word=word):
                self.assertEqual(s_stem(word), light)
                self.assertEqual(porter_stem(word), porter)


class CachedCollectionTests(unittest.TestCase):
    """Check caching and preserved document structure."""

    def test_cache_calls(self):
        """Each distinct word must invoke the stemmer only once."""

        stem = Mock(side_effect=porter_stem)

        documents = {
            7: ["flows", "flowing", "flows"],
            42: ["flowing"],
            99: [],
        }

        result, before, after, cache = stem_collection(documents, stem)

        self.assertEqual(stem.call_count, 2)

        self.assertEqual(result, {
            7: ["flow", "flow", "flow"],
            42: ["flow"],
            99: [],
        })

        self.assertEqual(dict(before), {
            "flows": 2,
            "flowing": 2,
        })

        self.assertEqual(dict(after), {
            "flow": 4,
        })

        self.assertEqual(cache, {
            "flows": "flow",
            "flowing": "flow",
        })

    def test_s_stemmer(self):
        """The collection function must support the S-stemmer too."""

        result, _, _, _ = stem_collection(
            {1: ["ponies", "horses", "flowing"]},
            s_stem,
        )

        self.assertEqual(result, {
            1: ["pony", "horse", "flowing"],
        })

    def test_empty_input(self):
        """An empty collection should produce empty outputs."""

        self.assertEqual(
            stem_collection({}, porter_stem),
            ({}, Counter(), Counter(), {}),
        )

    def test_input_unchanged(self):
        """Stemming must not modify the original token lists."""

        documents = {
            8: ["flows", "flowing"],
        }

        stem_collection(documents, porter_stem)

        self.assertEqual(documents, {
            8: ["flows", "flowing"],
        })


class NltkComparisonTests(unittest.TestCase):
    """Compare every word in each saved Phase 2 vocabulary with NLTK."""

    def test_whole_vocabularies(self):
        """Save agreement reports and detect stale maps or mismatches."""

        # NLTK is imported only inside this reference check.
        import nltk
        from nltk.stem.porter import PorterStemmer

        # The default NLTK mode adds extensions, so select original explicitly.
        reference = PorterStemmer(
            mode=PorterStemmer.ORIGINAL_ALGORITHM
        )

        summary = []

        for collection in ("med", "cran", "cisi", "lisa", "npl"):
            with self.subTest(collection=collection):
                folder = Path("out") / collection
                path = folder / "porter_word_stems.csv"

                self.assertTrue(
                    path.is_file(),
                    f"Run phase2 for {collection} first",
                )

                # This mapping contains one row per distinct input word.
                with path.open(
                    encoding="utf-8",
                    newline="",
                ) as stream:
                    rows = list(csv.DictReader(stream))

                stats = json.loads(
                    (folder / "phase2_stats.json").read_text(
                        encoding="utf-8"
                    )
                )

                # Check vocabulary size and reject duplicate word rows.
                self.assertEqual(
                    len(rows),
                    stats["methods"]["porter"]["M_before"],
                )
                self.assertEqual(
                    len({row["word"] for row in rows}),
                    len(rows),
                )

                mismatches = []
                stale = []
                fallback_words = []

                for row in rows:
                    word = row["word"]

                    # Recompute our result using the current implementation.
                    actual = porter_stem(word)
                    expected = reference.stem(word)

                    # Saved outputs must reflect the current code.
                    if (
                        row["raw_stem"] != actual
                        or row["output_stem"] != (actual or word)
                    ):
                        stale.append(word)

                    # Compare raw algorithm results without output fallback.
                    if actual != expected:
                        mismatches.append([
                            word,
                            actual,
                            expected,
                        ])

                    if not actual:
                        fallback_words.append(word)

                total = len(rows)
                matches = total - len(mismatches)

                agreement = (
                    100 * matches / total
                    if total
                    else None
                )

                report = {
                    "collection": collection,
                    "nltk_version": nltk.__version__,
                    "reference_mode": "ORIGINAL_ALGORITHM",
                    "comparison": (
                        "Raw porter_stem output against raw NLTK output."
                    ),
                    "vocabulary_size": total,
                    "matching_words": matches,
                    "mismatching_words": len(mismatches),
                    "agreement_percent": agreement,
                    "stale_saved_words": stale,
                    "empty_stem_fallback_words": fallback_words,
                    "empty_stem_note": (
                        "Output files preserve the original word when "
                        "the raw stem is empty. Raw comparison does "
                        "not apply this fallback."
                    ),
                }

                # Save results before assertions so failures can be inspected.
                (folder / "nltk_comparison.json").write_text(
                    json.dumps(report, indent=2) + "\n",
                    encoding="utf-8",
                )

                with (folder / "nltk_mismatches.csv").open(
                    "w",
                    encoding="utf-8",
                    newline="",
                ) as stream:
                    writer = csv.writer(stream)
                    writer.writerow([
                        "word",
                        "our_raw_stem",
                        "nltk_raw_stem",
                    ])
                    writer.writerows(mismatches)

                summary.append([
                    collection,
                    total,
                    matches,
                    len(mismatches),
                    agreement,
                    nltk.__version__,
                ])

                if agreement is not None:
                    print(
                        f"\n{collection.upper()}: "
                        f"{matches}/{total} raw stems agree "
                        f"({agreement:.2f}%)"
                    )

                self.assertEqual(
                    stale,
                    [],
                    "Saved maps are stale; rerun phase2",
                )
                self.assertEqual(
                    mismatches,
                    [],
                    "Inspect nltk_mismatches.csv",
                )

        # Save a combined table for all five collections.
        with (Path("out") / "nltk_comparison.csv").open(
            "w",
            encoding="utf-8",
            newline="",
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow([
                "collection",
                "vocabulary_size",
                "matching_words",
                "mismatching_words",
                "agreement_percent",
                "nltk_version",
            ])
            writer.writerows(summary)


if __name__ == "__main__":
    unittest.main()