# Phase 2 — Stemming

**Student:** Ahmad Zabet — **ID:** 32230137  
**Course:** CSCI512 Information Retrieval  
**Instructor:** Dr. Maysaa Khalil

**Co-authorship:** This implementation and report were co-authored by Ahmad Zabet and ChatGPT (OpenAI). ChatGPT contributed draft code, tests, debugging assistance, explanations, and documentation. Ahmad ran the project locally and reviewed the results.

## Method

Phase 2 reads the reviewed-stoplist outputs from `out/<collection>/stp/`. Our implementation applies Porter’s original 1980 rules, including contextual classification of `y`, measure `m`, suffix conditions, and Steps 1a–5b. Each step considers its longest matching suffix; a failed condition does not trigger a shorter suffix.

We also implemented Harman’s S-stemmer, which handles plural endings using three conditional rules. Each algorithm caches word-to-stem results, processing each distinct input word once per collection.

Porter outputs are saved as `out/<collection>/sfx/<doc_id>.sfx`; S-stemmer outputs use `out/<collection>/s_stemmer/sfx/`. Original IDs, order, repetitions, and empty documents are preserved.

Both raw algorithms turn the token `s` into an empty string. For file output, we retain the original token in this case and record the fallback. It occurs 25, 27, 27, 46, and 118 times in MEDLINE, CRAN, CISI, LISA, and NPL respectively. Raw algorithm comparisons do not apply this fallback.

## Vocabulary results

Here, \(M\) counts distinct terms and \(ICF=(M_{\text{before}}-M_{\text{after}})/M_{\text{before}}\). ICF measures vocabulary reduction, not serialized file-size reduction.

| Collection | Documents | M before | Porter M after | Porter ICF | S-stemmer M after | S-stemmer ICF |
|---|---:|---:|---:|---:|---:|---:|
| MEDLINE | 1,033 | 13,494 | 9,905 | 0.2660 | 12,278 | 0.0901 |
| CRAN | 1,400 | 7,776 | 5,141 | 0.3389 | 6,828 | 0.1219 |
| CISI | 1,460 | 10,084 | 6,285 | 0.3767 | 8,760 | 0.1313 |
| LISA | 5,999 | 19,225 | 13,439 | 0.3010 | 16,963 | 0.1177 |
| NPL | 11,429 | 12,170 | 7,972 | 0.3449 | 10,476 | 0.1392 |

Token counts before and after stemming remain equal: MEDLINE 105,361; CRAN 154,566; CISI 117,769; LISA 346,012; NPL 308,222.

Porter reduces vocabulary more than the S-stemmer in every collection. This demonstrates stronger conflation, but does not establish better retrieval effectiveness.

## Ten largest Porter conflation classes

Numbers in parentheses count distinct original word forms. Classes are ranked by this count, with alphabetical stem order breaking ties. Complete memberships and occurrence counts are saved in each collection’s `porter_conflation_classes.json`.

| Collection | Ten largest classes |
|---|---|
| MEDLINE | oper (12), indic (10), organ (10), commun (9), concentr (9), gener (9), potenti (9), determin (8), differ (8), infect (8) |
| CRAN | gener (15), observ (11), oper (10), deriv (9), determin (9), integr (9), comput (8), continu (8), indic (8), investig (8) |
| CISI | gener (20), design (11), oper (11), adapt (10), comput (10), continu (10), inform (10), origin (10), predict (10), select (10) |
| LISA | gener (16), commun (13), indic (12), oper (12), origin (12), continu (11), inform (11), access (10), collect (10), consult (10) |
| NPL | gener (16), magnet (11), altern (10), deriv (10), determin (10), equal (10), indic (10), modul (10), observ (10), oper (10) |

## Five observed stemming limitations

All words below occur in the supplied LISA collection. Counts are token occurrences before stemming.

| Word pair and counts | Porter stems | Assessment |
|---|---|---|
| university (1,223), universe (4) | univers, univers | Over-stemming: institution and universe are different concepts. |
| general (538), generous (5) | gener, gener | Over-stemming: generality and generosity are different meanings. |
| experimental (64), experiments (40) | experiment, experi | Under-stemming: related forms remain separate. |
| matrix (17), matrices (1) | matrix, matric | Under-stemming: singular and plural remain separate. |
| absorb (2), absorption (2) | absorb, absorpt | Under-stemming: related verb and noun remain separate. |

For contextual confirmation, LISA document 1 contains “UNIVERSITY LIBRARIANSHIP COURSES”; document 173 contains “SPECIAL LIBRARY UNIVERSE”; document 2014 contains “GENEROUS FUNDING”. These observations illustrate semantic limitations, rather than implementation mismatches.

## Validation and reproducibility

The suite passes 57 tests, including 31 stemming tests. Checks cover conditions, suffix rules, required lecture examples, caching, preserved document structure, and whole-vocabulary comparison.

Using NLTK 3.10.4 with `PorterStemmer.ORIGINAL_ALGORITHM`, raw stems agree on 100% of each saved vocabulary: 13,494 MEDLINE, 7,776 CRAN, 10,084 CISI, 19,225 LISA, and 12,170 NPL words. There are zero mismatches. NLTK is used only in tests.

Run from the repository root:

```powershell
python -m pip install -r requirements.txt
python -B run.py phase2 --collection all
python -B -m unittest discover -s tests -v
```

Recorded Phase 2 runtimes were 1.3976, 1.3986, 1.7929, 5.4942, and 8.5115 seconds for MEDLINE, CRAN, CISI, LISA, and NPL respectively. These cover both algorithms and most output writing, excluding the final statistics-file write. Runtime varies between runs.