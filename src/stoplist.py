"""Stopword selection and a simple index for size comparisons."""

from collections import Counter, defaultdict
import json


def count_terms(documents):
    """Count occurrences (cf) and documents containing each term (df)."""
    cf, df = Counter(), Counter()

    for tokens in documents.values():
        cf.update(tokens)
        df.update(set(tokens))

    return cf, df


def build_stoplist(df, document_count, threshold=0.5):
    """Pure automatic rule: select every term with df/N >= threshold."""
    if not 0 < threshold <= 1:
        raise ValueError(
            "threshold must be greater than 0 and at most 1"
        )

    if document_count < 0:
        raise ValueError("document_count cannot be negative")

    if document_count == 0:
        if df:
            raise ValueError(
                "An empty collection cannot have term frequencies"
            )
        return set()

    if any(not 1 <= count <= document_count for count in df.values()):
        raise ValueError(
            "Every df must be between 1 and document_count"
        )

    return {
        word
        for word, count in df.items()
        if count / document_count >= threshold
    }


def remove_stopwords(tokens, stopwords):
    """Keep the order and repetitions of retained terms."""
    return [
        token
        for token in tokens
        if token not in stopwords
    ]


def comparison_index_bytes(documents):
    """Serialize term -> [[doc_id, tf], ...] as compact UTF-8 JSON.

    This unstemmed index is only for consistent size comparisons.
    It does not implement Phase 3 weights or document norms.
    """
    postings = defaultdict(list)

    for doc_id in sorted(documents):
        for term, tf in Counter(documents[doc_id]).items():
            postings[term].append([doc_id, tf])

    return json.dumps(
        postings,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")