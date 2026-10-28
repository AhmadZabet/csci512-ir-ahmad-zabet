"""Tests for pure DF selection, filtering, and comparison indexes."""

import json
import unittest

from src.stoplist import (
    count_terms,
    build_stoplist,
    remove_stopwords,
    comparison_index_bytes,
)


class StoplistTests(unittest.TestCase):
    def test_cf_and_df_are_different(self):
        cf, df = count_terms({
            1: ["the", "flow", "flow"],
            2: ["the", "wing"],
            3: [],
        })

        self.assertEqual(
            dict(cf),
            {"the": 2, "flow": 2, "wing": 1},
        )
        self.assertEqual(
            dict(df),
            {"the": 2, "flow": 1, "wing": 1},
        )

    def test_threshold_is_inclusive(self):
        self.assertEqual(
            build_stoplist(
                {"the": 4, "and": 2, "wing": 1},
                4,
                0.5,
            ),
            {"the", "and"},
        )

    def test_automatic_has_no_topical_exceptions(self):
        self.assertEqual(
            build_stoplist(
                {"flow": 2, "library": 3, "the": 4},
                4,
                0.5,
            ),
            {"flow", "library", "the"},
        )

    def test_empty_documents_count_in_n(self):
        _, df = count_terms({
            1: ["the"],
            2: [],
        })

        self.assertEqual(
            build_stoplist(df, 2, 0.6),
            set(),
        )

    def test_filter_preserves_order_and_input(self):
        tokens = ["the", "flow", "and", "flow", "wing"]

        self.assertEqual(
            remove_stopwords(tokens, {"the", "and"}),
            ["flow", "flow", "wing"],
        )
        self.assertEqual(
            tokens,
            ["the", "flow", "and", "flow", "wing"],
        )

    def test_empty_inputs(self):
        cf, df = count_terms({})

        self.assertEqual(dict(cf), {})
        self.assertEqual(dict(df), {})
        self.assertEqual(build_stoplist(df, 0), set())
        self.assertEqual(remove_stopwords([], {"the"}), [])

    def test_invalid_inputs(self):
        for threshold in (0, -0.5, 1.1, float("nan")):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    build_stoplist({"the": 1}, 1, threshold)

        for df, n in [
            ({"the": 2}, 1),
            ({"the": 1}, 0),
            ({}, -1),
        ]:
            with self.subTest(df=df, n=n):
                with self.assertRaises(ValueError):
                    build_stoplist(df, n)

    def test_index_preserves_ids_counts_and_sort_order(self):
        data = comparison_index_bytes({
            10: ["wing", "flow", "flow"],
            2: ["flow"],
            7: [],
        })

        self.assertEqual(
            json.loads(data),
            {
                "flow": [[2, 1], [10, 2]],
                "wing": [[10, 1]],
            },
        )

    def test_index_serialization_is_reproducible(self):
        left = {
            10: ["wing", "flow"],
            2: ["flow"],
        }
        right = {
            2: ["flow"],
            10: ["flow", "wing"],
        }

        self.assertEqual(
            comparison_index_bytes(left),
            comparison_index_bytes(right),
        )
        self.assertEqual(
            comparison_index_bytes({}),
            b"{}",
        )


if __name__ == "__main__":
    unittest.main()