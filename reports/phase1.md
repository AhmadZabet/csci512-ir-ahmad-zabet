# Phase 1 — Parsing, Tokenization, and Stoplists

**Ahmad Zabet — 32230137 | CSCI512 | 29 October 2026**

**Co-authorship disclosure:** This implementation and report were co-authored by Ahmad Zabet and ChatGPT (OpenAI). ChatGPT contributed draft code, tests, debugging assistance, explanations, and documentation. Ahmad ran the project locally, reviewed outputs, and discussed design choices and results.

## Method and decisions

**Parsing:** MEDLINE retains `.W`; CRAN and CISI retain `.T` plus `.W`. CRAN’s repeated title is retained as specified. NPL uses numeric IDs and `/` record endings. LISA uses `Document n` headers and asterisk separators across 14 files. Original document IDs are preserved for later relevance evaluation.

**Tokenization:** Lowercase; join dotted acronyms; retain integers, decimals, and alphanumeric terms; remove thousands-group commas; split hyphens and other punctuation; normalize curly apostrophes, remove ending `'s`, then delete remaining apostrophes. Matching uses ASCII letters and digits. Token order and repetitions are preserved. These rules improve consistency but can merge distinctions: `U.S.` becomes `us`, and numeric signs are discarded.

**Reviewed stoplists:** Following the instructor’s clarification that students must construct their lists, the top 50 terms by collection frequency were inspected separately for each collection. Common grammatical terms were selected for low expected topical discrimination. Technical terms, numbers, negation, and ambiguous terms were retained conservatively. Reviewed-list sizes are 28, 24, 29, 27, and 19 for MEDLINE, CRAN, CISI, LISA, and NPL.

**Automatic stoplists:** Independently select every term with `df/N ≥ 0.5`, without manual exceptions. The 0.5 threshold is a reproducible starting choice, not an optimum established by retrieval evaluation. Thresholds 0.4 and 0.6 are also compared. Manual words use the same tokenizer as documents; generated words already come from normalized tokens. Sets provide efficient membership checks.

## Main results: reviewed stoplists

`N` is documents, `T` is total token occurrences, and `M` is distinct terms. Removal percentage is `100 × (T_before − T_after) / T_before`.

| Collection | N | T before | T after | Removed | M before | M after |
|---|---:|---:|---:|---:|---:|---:|
| MEDLINE | 1,033 | 159,443 | 105,361 | 33.92% | 13,522 | 13,494 |
| CRAN | 1,400 | 241,832 | 154,566 | 36.09% | 7,800 | 7,776 |
| CISI | 1,460 | 186,968 | 117,769 | 37.01% | 10,113 | 10,084 |
| LISA | 5,999 | 524,897 | 346,012 | 34.08% | 19,252 | 19,225 |
| NPL | 11,429 | 479,163 | 308,222 | 35.67% | 12,189 | 12,170 |

## Automatic results and index-size comparison

Index sizes are actual bytes of identically serialized, unstemmed `term → [[doc_id, tf], ...]` indexes. They do not represent Phase 3 weighted indexes.

| Collection | Auto words | Auto T after | Auto removed | Auto M after | Reviewed bytes | Auto bytes |
|---|---:|---:|---:|---:|---:|---:|
| MEDLINE | 11 | 116,032 | 27.23% | 13,511 | 780,596 | 831,178 |
| CRAN | 16 | 160,739 | 33.53% | 7,784 | 928,237 | 961,128 |
| CISI | 13 | 129,967 | 30.49% | 10,100 | 885,406 | 949,618 |
| LISA | 9 | 379,546 | 27.69% | 19,243 | 2,697,009 | 2,927,550 |
| NPL | 5 | 369,219 | 22.95% | 12,184 | 2,568,566 | 2,963,639 |

## Top 20 terms after reviewed-list removal

Terms are listed in descending occurrence count; ties use alphabetical order.

**MEDLINE:** or (658), patients (646), not (606), cells (542), after (437), cases (374), 2 (365), normal (351), but (349), growth (338), may (327), blood (314), during (312), than (309), 1 (293), found (289), treatment (285), children (272), other (269), cell (261).

**CRAN:** flow (2,179), boundary (1,371), pressure (1,330), layer (1,189), number (1,031), mach (911), results (896), theory (872), shock (795), heat (749), method (737), two (693), wing (641), supersonic (629), surface (623), body (600), effects (598), transfer (581), temperature (564), obtained (542).

**CISI:** information (1,595), library (1,273), system (770), or (748), libraries (612), data (601), research (571), retrieval (557), use (526), not (514), systems (496), science (459), one (457), more (453), some (421), scientific (399), can (391), book (367), study (362), other (346).

**LISA:** library (7,912), information (5,276), libraries (4,223), services (1,977), system (1,941), public (1,924), data (1,865), use (1,531), research (1,379), systems (1,355), new (1,353), development (1,335), national (1,241), university (1,223), librarians (1,127), service (1,119), not (1,069), report (977), education (963), or (960).

**NPL:** frequency (2,465), field (2,015), magnetic (2,006), described (1,550), theory (1,538), circuit (1,527), electron (1,486), given (1,479), results (1,415), two (1,385), between (1,300), discussed (1,232), method (1,223), radio (1,217), using (1,199), high (1,157), amplifier (1,109), circuits (1,094), analysis (1,058), or (987).

## Findings, limitations, and validation

Small reviewed lists remove 33.92–37.01% of token occurrences while removing few vocabulary entries, consistent with frequent words accounting for much of a collection. Their indexes are smaller than the automatic-list indexes in this run. The automatic rule removes `flow` in CRAN and `library` in LISA; the reviewed lists retain these topical terms. Storage reduction alone does not establish retrieval quality. Reviewing only the top 50 terms also leaves potentially removable grammatical words outside the inspected range.

The instructor corrected LISA’s required count to 5,999. Its archive contains four identical duplicate records and seven text lines outside document boundaries; duplicates are counted once and those lines are skipped with a warning. Missing IDs are not invented. CRAN’s empty records 471 and 995 are preserved.

All 26 tests pass. Main outputs preserve IDs and term order in `out/<collection>/stp/`. Automatic lists, alternative outputs, per-word reasons, threshold comparisons, top terms, and size statistics are reproducible using `python run.py phase1 --collection all`. Data and generated outputs are excluded from Git.