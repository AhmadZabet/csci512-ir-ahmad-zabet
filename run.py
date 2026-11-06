"""Run Phase 1 stoplist processing and Phase 2 stemming."""

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from time import perf_counter

from src.parsers import (
    parse_medline,
    parse_cran,
    parse_cisi,
    parse_lisa,
    parse_npl,
)
from src.stoplist import (
    count_terms,
    build_stoplist,
    remove_stopwords,
    comparison_index_bytes,
)
from src.text_ops import tokenize
from src.stemmer import porter_stem, s_stem, stem_collection


# Parser, raw-data location, and expected document count.
COLLECTIONS = {
    "med": (parse_medline, "data/med/MED.ALL", 1033),
    "cran": (parse_cran, "data/cran/cran.all.1400", 1400),
    "cisi": (parse_cisi, "data/cisi/CISI.ALL", 1460),
    "lisa": (parse_lisa, "data/lisa", 5999),
    "npl": (parse_npl, "data/npl/doc-text", 11429),
}

# Manually reviewed grammatical selections from the top 50 words by cf.
REVIEWED = {
    "med": (
        "a an and are as at be been by for from had has have in is it "
        "of on that the these this to was were which with"
    ),
    "cran": (
        "a an and are as at be been by for from in is it of on that "
        "the this to was were which with"
    ),
    "cisi": (
        "a an and are as at be been by for from has have in is it its "
        "of on that the their these this to was were which with"
    ),
    "lisa": (
        "a an and are as at be by for from has have in is it its of on "
        "that the their this to was were which with"
    ),
    "npl": (
        "a an and are as at be by for from in is of on that the to "
        "which with"
    ),
}

REASON_GROUPS = [
    (
        "a an the",
        "Article; low expected topical discrimination.",
    ),
    (
        "are be been had has have is was were",
        "Common verb form; low expected topical discrimination.",
    ),
    (
        "it its that their these this which",
        "Reference word; low expected topical discrimination.",
    ),
    (
        "and as at by for from in of on to with",
        "Connector or preposition; low expected topical discrimination.",
    ),
]


def ranked(counter):
    """Sort by descending frequency, with alphabetical tie-breaking."""

    return sorted(
        counter.items(),
        key=lambda item: (-item[1], item[0]),
    )


def reduction(before, after):
    """Return percentage reduction, handling an empty starting value."""

    return 100 * (before - after) / before if before else 0.0


def reviewed_reason(word):
    """Return the justification for a manually reviewed stopword."""

    for words, reason in REASON_GROUPS:
        if word in words.split():
            return reason

    raise ValueError(
        f"Missing justification for reviewed word: {word}"
    )


def write_csv(path, header, rows):
    """Write a UTF-8 CSV file with its header."""

    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def write_stoplist(path, words):
    """Save sorted stopwords, one per line."""

    path.write_text(
        "".join(word + "\n" for word in sorted(words)),
        encoding="utf-8",
    )


def run_phase1(name, threshold):
    """Parse, tokenize, filter, and compare Phase 1 stoplist methods."""

    started = perf_counter()

    parser, input_path, expected = COLLECTIONS[name]
    documents = parser(input_path)

    if len(documents) != expected:
        raise ValueError(
            f"{name}: expected {expected} documents, "
            f"got {len(documents)}"
        )

    tokens = {
        doc_id: tokenize(text)
        for doc_id, text in documents.items()
    }

    cf, df = count_terms(tokens)

    n = len(tokens)
    total = sum(cf.values())
    vocabulary = len(cf)

    # Normalize stopwords with the same tokenizer as document text.
    reviewed = set(tokenize(REVIEWED[name]))
    automatic = build_stoplist(df, n, threshold)

    output = Path("out") / name
    output.mkdir(parents=True, exist_ok=True)

    write_stoplist(output / "reviewed_stoplist.txt", reviewed)
    write_stoplist(output / "own_stoplist.txt", automatic)

    # Record both methods' decisions for every vocabulary term.
    word_rows = []

    for word, occurrences in ranked(cf):
        coverage = df[word] / n

        word_rows.append([
            word,
            occurrences,
            df[word],
            round(100 * occurrences / total, 4) if total else 0,
            round(100 * coverage, 4),
            "REMOVE" if word in reviewed else "KEEP",
            (
                reviewed_reason(word)
                if word in reviewed
                else "Not selected for the reviewed list."
            ),
            "REMOVE" if word in automatic else "KEEP",
            (
                f"df/N={coverage:.6f}; "
                f"threshold={threshold:g}; no exceptions."
            ),
        ])

    write_csv(
        output / "word_statistics.csv",
        [
            "word",
            "cf",
            "df",
            "token_share_percent",
            "coverage_percent",
            "reviewed_decision",
            "reviewed_reason",
            "automatic_decision",
            "automatic_reason",
        ],
        word_rows,
    )

    results = {}
    comparison_rows = []
    baseline_bytes = 0

    for method, stop in [
        ("baseline", set()),
        ("reviewed", reviewed),
        ("automatic", automatic),
    ]:
        filtered = {
            doc_id: remove_stopwords(terms, stop)
            for doc_id, terms in tokens.items()
        }

        after_cf, after_df = count_terms(filtered)
        after_total = sum(after_cf.values())

        method_dir = output / method
        method_dir.mkdir(parents=True, exist_ok=True)

        index_data = comparison_index_bytes(filtered)
        (method_dir / "comparison_index.json").write_bytes(index_data)
        size = len(index_data)

        if method == "baseline":
            baseline_bytes = size
        else:
            stp_dir = (
                output / "stp"
                if method == "reviewed"
                else method_dir / "stp"
            )
            stp_dir.mkdir(parents=True, exist_ok=True)

            for doc_id, terms in filtered.items():
                (stp_dir / f"{doc_id}.stp").write_text(
                    " ".join(terms) + "\n",
                    encoding="utf-8",
                )

        stats = {
            "stoplist_size": len(stop),
            "T_before": total,
            "T_after": after_total,
            "tokens_removed_percent": reduction(total, after_total),
            "M_before": vocabulary,
            "M_after": len(after_cf),
            "postings": sum(after_df.values()),
            "comparison_index_bytes": size,
            "index_reduction_percent": reduction(baseline_bytes, size),
            "empty_token_documents": sum(
                not terms for terms in filtered.values()
            ),
            "top_20_after": ranked(after_cf)[:20],
        }

        results[method] = stats

        comparison_rows.append([
            method,
            n,
            len(stop),
            total,
            after_total,
            round(stats["tokens_removed_percent"], 4),
            vocabulary,
            len(after_cf),
            stats["postings"],
            size,
            round(stats["index_reduction_percent"], 4),
        ])

    write_csv(
        output / "comparison.csv",
        [
            "method",
            "N",
            "stoplist_size",
            "T_before",
            "T_after",
            "tokens_removed_percent",
            "M_before",
            "M_after",
            "postings",
            "comparison_index_bytes",
            "index_reduction_percent",
        ],
        comparison_rows,
    )

    threshold_rows = []

    for value in sorted({0.4, 0.5, 0.6, threshold}):
        stop = build_stoplist(df, n, value)
        remaining = total - sum(cf[word] for word in stop)

        threshold_rows.append([
            value,
            len(stop),
            remaining,
            vocabulary - len(stop),
            round(reduction(total, remaining), 4),
        ])

    write_csv(
        output / "threshold_comparison.csv",
        [
            "threshold",
            "stoplist_size",
            "T_after",
            "M_after",
            "removed_percent",
        ],
        threshold_rows,
    )

    report = {
        "collection": name,
        "N": n,
        "automatic_threshold": threshold,
        "main_stp_method": "reviewed",
        "reviewed_policy": (
            "Manual grammatical selections from top 50 by cf."
        ),
        "automatic_policy": (
            "df/N >= threshold; no manual exceptions."
        ),
        "index_format": (
            "Unstemmed term -> [[doc_id, tf]]; compact UTF-8 JSON."
        ),
        "top_20_before": ranked(cf)[:20],
        "top_20_by_df": ranked(df)[:20],
        "methods": results,
        "runtime_seconds": round(perf_counter() - started, 4),
    }

    (output / "phase1_stats.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n{name.upper()} | N={n}")
    print("Reviewed:", ", ".join(sorted(reviewed)))
    print("Automatic:", ", ".join(sorted(automatic)))

    print(
        f"{'Method':<12} {'Words':>6} "
        f"{'T after':>10} {'M after':>9} "
        f"{'Removed':>9} {'Index bytes':>12}"
    )

    for method, stats in results.items():
        print(
            f"{method:<12} {stats['stoplist_size']:>6} "
            f"{stats['T_after']:>10} {stats['M_after']:>9} "
            f"{stats['tokens_removed_percent']:>8.2f}% "
            f"{stats['comparison_index_bytes']:>12}"
        )

    print("Outputs:", output)
    return report


def read_stp(name):
    """Read Phase 1 token files without tokenizing their contents again."""

    folder = Path("out") / name / "stp"
    paths = list(folder.glob("*.stp"))

    if not paths:
        raise FileNotFoundError(
            f"No .stp files in {folder}; run phase1 first"
        )

    # Validate filenames before converting their IDs to integers.
    for path in paths:
        if not path.stem.isdecimal() or int(path.stem) < 1:
            raise ValueError(
                f"Invalid document filename: {path.name}"
            )

    documents = {}

    for path in sorted(paths, key=lambda item: int(item.stem)):
        doc_id = int(path.stem)

        if doc_id in documents:
            raise ValueError(f"Duplicate document ID: {doc_id}")

        # .stp already contains normalized, stopped tokens.
        # An empty file correctly becomes an empty list.
        documents[doc_id] = path.read_text(
            encoding="utf-8"
        ).split()

    expected = COLLECTIONS[name][2]

    if len(documents) != expected:
        raise ValueError(
            f"{name}: expected {expected} documents, "
            f"got {len(documents)}"
        )

    return documents


def run_phase2(name):
    """Stem Phase 1 documents and compare Porter with the S-stemmer."""

    started = perf_counter()
    documents = read_stp(name)
    output = Path("out") / name

    methods = {}
    comparison_rows = []

    for method, stem in (
        ("porter", porter_stem),
        ("s_stemmer", s_stem),
    ):
        # Keep raw results so the empty-stem policy remains auditable.
        raw_cache = {}

        def safe_stem(word):
            """Preserve the original token if its raw stem is empty."""

            raw_cache[word] = stem(word)
            return raw_cache[word] or word

        # stem_collection calls safe_stem once per distinct word.
        stemmed, before, after, cache = stem_collection(
            documents,
            safe_stem,
        )

        # Stemming must preserve token occurrences and document lengths.
        if sum(before.values()) != sum(after.values()):
            raise ValueError(f"{method}: token count changed")

        for doc_id in documents:
            if len(documents[doc_id]) != len(stemmed[doc_id]):
                raise ValueError(
                    f"{method}: token count changed in {doc_id}"
                )

        # Main Porter output uses the handout's required path.
        target = (
            output / "sfx"
            if method == "porter"
            else output / "s_stemmer" / "sfx"
        )
        target.mkdir(parents=True, exist_ok=True)

        # Detect stale documents rather than silently leaving extra files.
        expected_names = {
            f"{doc_id}.sfx"
            for doc_id in documents
        }
        extra = {
            path.name
            for path in target.glob("*.sfx")
        } - expected_names

        if extra:
            raise ValueError(
                f"Unexpected old .sfx files in {target}: "
                f"{sorted(extra)[:5]}"
            )

        for doc_id, terms in stemmed.items():
            (target / f"{doc_id}.sfx").write_text(
                " ".join(terms) + "\n",
                encoding="utf-8",
            )

        # A conflation class contains original words sharing one stem.
        # Store each original word's collection frequency as well.
        groups = defaultdict(dict)

        for word, result in cache.items():
            groups[result][word] = before[word]

        classes = [
            {
                "stem": result,
                "size": len(words),
                "token_count": sum(words.values()),
                "words": dict(sorted(words.items())),
            }
            for result, words in groups.items()
        ]

        # Largest means most distinct original word forms.
        classes.sort(
            key=lambda item: (-item["size"], item["stem"])
        )

        m_before = len(before)
        m_after = len(after)

        # ICF is a fraction, not a percentage or an on-disk byte measure.
        icf = (
            (m_before - m_after) / m_before
            if m_before
            else 0.0
        )

        fallback = {
            word: before[word]
            for word, result in raw_cache.items()
            if not result
        }

        stats = {
            "M_before": m_before,
            "M_after": m_after,
            "ICF": icf,
            "vocabulary_reduction_percent": 100 * icf,
            "T_before": sum(before.values()),
            "T_after": sum(after.values()),
            "cache_size": len(cache),
            "empty_stem_fallback": fallback,
            "top_10_conflation_classes": classes[:10],
        }

        methods[method] = stats

        # Save all classes, including single-word classes, for inspection.
        (output / f"{method}_conflation_classes.json").write_text(
            json.dumps(classes, indent=2) + "\n",
            encoding="utf-8",
        )

        # Save raw and output stems separately.
        write_csv(
            output / f"{method}_word_stems.csv",
            [
                "word",
                "cf",
                "raw_stem",
                "output_stem",
                "empty_fallback",
            ],
            (
                [
                    word,
                    before[word],
                    raw_cache[word],
                    cache[word],
                    not bool(raw_cache[word]),
                ]
                for word in sorted(cache)
            ),
        )

        comparison_rows.append([
            method,
            len(documents),
            m_before,
            m_after,
            round(icf, 6),
            round(100 * icf, 4),
            sum(after.values()),
            len(cache),
        ])

        print(
            f"{name.upper()} | {method}: "
            f"M {m_before} -> {m_after}, ICF={icf:.4f}"
        )

        if fallback:
            print(
                "Empty-stem fallback (word: occurrences):",
                fallback,
            )

    write_csv(
        output / "stemming_comparison.csv",
        [
            "method",
            "N",
            "M_before",
            "M_after",
            "ICF",
            "vocabulary_reduction_percent",
            "T_after",
            "cache_size",
        ],
        comparison_rows,
    )

    report = {
        "collection": name,
        "N": len(documents),
        "input": f"out/{name}/stp",
        "main_sfx_method": "porter",
        "empty_stem_policy": (
            "Preserve original token when the raw stem is empty; "
            "report each case."
        ),
        "class_ranking": (
            "Distinct original word forms descending, "
            "then stem alphabetically."
        ),
        "methods": methods,
        "runtime_seconds": round(perf_counter() - started, 4),
    }

    (output / "phase2_stats.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    return report


def main():
    """Read command-line options and run the selected phase."""

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "phase",
        choices=["phase1", "phase2"],
    )
    parser.add_argument(
        "--collection",
        choices=["all", *COLLECTIONS],
        default="all",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Automatic stoplist threshold used by Phase 1.",
    )

    args = parser.parse_args()

    if not 0 < args.threshold <= 1:
        parser.error(
            "--threshold must be greater than 0 and at most 1"
        )

    names = (
        COLLECTIONS
        if args.collection == "all"
        else [args.collection]
    )

    for name in names:
        if args.phase == "phase1":
            run_phase1(name, args.threshold)
        else:
            run_phase2(name)


if __name__ == "__main__":
    main()