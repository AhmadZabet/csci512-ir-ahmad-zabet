# CSCI512 — Build Your Own Search Engine

**Student:** Ahmad Zabet  
**Student ID:** 32230137  
**Course:** CSCI512 Information Retrieval, Fall 2026  
**Instructor:** Dr. Maysaa Khalil  
**Python:** 3.15.2 used for local testing; Python 3.10 or later required.

## Co-authorship: Chatgpt+

## Current implementation

Phase 1 implements:

- Parsing MEDLINE, CRAN, CISI, LISA, and NPL.
- Tokenization and normalization.
- Manually reviewed, collection-specific stoplists.
- Automatic stoplists using document frequency.
- Stopword filtering and one `.stp` file per document.
- Frequency statistics and comparisons between both stoplist methods.
- Simple unstemmed indexes for reproducible storage comparisons.

Phases 2–5 are not implemented yet.

## Installation

The current implementation uses only the Python standard library. No third-party packages are required, so `requirements.txt` is empty.

From the repository root:

```powershell
python --version
python -m pip install -r requirements.txt
```

## Data setup

Download and extract the collections from the [University of Glasgow test collections site](https://ir.dcs.gla.ac.uk/resources/test_collections/).

Place the document files as follows:

```text
data/
├── med/MED.ALL
├── cran/cran.all.1400
├── cisi/CISI.ALL
├── lisa/
│   ├── LISA0.001
│   ├── LISA0.501
│   └── ... all 14 LISA document parts
└── npl/doc-text
```

Keep the accompanying queries and relevance judgments for later phases. For LISA evaluation, use `LISARJ.NUM`, not the older `LISA.REL`.

The instructor clarified that the supplied LISA collection should contain **5,999 distinct documents**, replacing the handout’s original count. The instructor also clarified that students must construct and justify their stoplists rather than receive a supplied list.

Neither `data/` nor `out/` is committed.

## Running Phase 1

Run all commands from the repository root.

Process every collection:

```powershell
python run.py phase1 --collection all
```

Process one collection:

```powershell
python run.py phase1 --collection med
```

The available collection codes are `med`, `cran`, `cisi`, `lisa`, and `npl`.

Choose another automatic document-coverage threshold:

```powershell
python run.py phase1 --collection all --threshold 0.4
```

The default threshold is `0.5`. Changing it affects the automatic list; the reviewed selections remain fixed. Runs update generated files under `out/`.

## Stoplist methods

**Reviewed:** inspect each collection’s top 50 terms by total occurrences and select common grammatical words with low expected topical discrimination. Decisions and reasons are documented. Potentially meaningful terms such as `flow`, `library`, and `not` are retained.

**Automatic:** include every term satisfying `df/N >= threshold`, where `df` counts documents containing the term and `N` includes all parsed documents. There are no manual exceptions. At the default threshold, this method removes `flow` in CRAN and `library` in LISA.

The main `.stp` outputs use the reviewed lists. Automatic outputs are stored separately for comparison.

## Outputs

For each collection, `out/<collection>/` contains:

| Output | Purpose |
|---|---|
| `reviewed_stoplist.txt` | Reviewed stopwords |
| `own_stoplist.txt` | Automatically generated stopwords |
| `stp/<doc_id>.stp` | Main outputs using the reviewed list |
| `automatic/stp/<doc_id>.stp` | Outputs using the automatic list |
| `word_statistics.csv` | Occurrences, document coverage, both decisions, and reasons |
| `comparison.csv` | Token, vocabulary, postings, and index-size comparison |
| `threshold_comparison.csv` | Automatic results for 0.4, 0.5, 0.6, and the selected threshold |
| `phase1_stats.json` | Statistics, top terms, policies, and runtime |
| `baseline/comparison_index.json` | Index without stopword removal |
| `reviewed/comparison_index.json` | Index after reviewed-list filtering |
| `automatic/comparison_index.json` | Index after automatic-list filtering |

Comparison indexes map each term to `[document_id, term_frequency]` pairs. All use identical compact UTF-8 JSON serialization. Their byte counts measure actual files, but these are unstemmed comparison indexes, not the final Phase 3 weighted indexes.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The current suite contains **26 passing tests** covering parsing, document counts, tokenization, document frequency, filtering, and comparison-index serialization.

## Data handling

- MEDLINE: retain `.W`.
- CRAN and CISI: retain `.T` and `.W`; ignore other fields.
- CRAN’s title is also present in `.W`; both copies are retained.
- CRAN records 471 and 995 are empty and retain their IDs.
- LISA: retain original IDs, count four identical duplicate records once, and skip seven text lines outside document boundaries with a warning. Conflicting copies raise an error.
- NPL: numeric IDs start records and `/` ends them.

Whitespace normalization preserves text content for tokenization. Detailed tokenization rules are documented in `src/text_ops.py`.

## Recorded runtime

The saved local run recorded these per-collection processing times:

| Collection | Documents | Seconds |
|---|---:|---:|
| MEDLINE | 1,033 | 2.6299 |
| CRAN | 1,400 | 3.0415 |
| CISI | 1,460 | 2.7853 |
| LISA | 5,999 | 16.7833 |
| NPL | 11,429 | 17.8706 |

These times include parsing, tokenization, comparisons, and most output writing. The timer is recorded before the final statistics-file write and console summary. Times vary between runs.

The Phase 1 report is in `reports/phase1.md`.
