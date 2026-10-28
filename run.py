"""Compare reviewed and automatic stoplists for Phase 1."""

import argparse
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


COLLECTIONS = {
    "med": (parse_medline, "data/med/MED.ALL", 1033),
    "cran": (parse_cran, "data/cran/cran.all.1400", 1400),
    "cisi": (parse_cisi, "data/cisi/CISI.ALL", 1460),
    "lisa": (parse_lisa, "data/lisa", 5999),
    "npl": (parse_npl, "data/npl/doc-text", 11429),
}

# Reviewed selections from each collection's top 50 terms by cf.
# These are fixed manual choices, not automatic threshold results.
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
    return sorted(
        counter.items(),
        key=lambda item: (-item[1], item[0]),
    )


def reduction(before, after):
    return (
        100 * (before - after) / before
        if before
        else 0.0
    )


def reviewed_reason(word):
    for words, reason in REASON_GROUPS:
        if word in words.split():
            return reason

    raise ValueError(
        f"Missing justification for reviewed word: {word}"
    )


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def write_stoplist(path, words):
    path.write_text(
        "".join(word + "\n" for word in sorted(words)),
        encoding="utf-8",
    )


def run_phase1(name, threshold):
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

    reviewed = set(tokenize(REVIEWED[name]))
    automatic = build_stoplist(df, n, threshold)

    output = Path("out") / name
    output.mkdir(parents=True, exist_ok=True)

    write_stoplist(
        output / "reviewed_stoplist.txt",
        reviewed,
    )
    write_stoplist(
        output / "own_stoplist.txt",
        automatic,
    )

    # Record both decisions independently for every vocabulary term.
    word_rows = []

    for word, occurrences in ranked(cf):
        coverage = df[word] / n

        word_rows.append([
            word,
            occurrences,
            df[word],
            (
                round(100 * occurrences / total, 4)
                if total
                else 0
            ),
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
            # The main pipeline uses reviewed terms.
            # Automatic terms go into a separate comparison folder.
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
            "tokens_removed_percent": reduction(
                total,
                after_total,
            ),
            "M_before": vocabulary,
            "M_after": len(after_cf),
            "postings": sum(after_df.values()),
            "comparison_index_bytes": size,
            "index_reduction_percent": reduction(
                baseline_bytes,
                size,
            ),
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

    # Replace the previous hybrid comparison with pure DF results.
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
        "runtime_seconds": round(
            perf_counter() - started,
            4,
        ),
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "phase",
        choices=["phase1"],
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
        run_phase1(name, args.threshold)


if __name__ == "__main__":
    main()