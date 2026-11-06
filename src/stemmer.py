"""Original Porter 1980 rules, Harman's S-stemmer, and cached stemming.

Inputs are lowercase tokens from the normalization pipeline.
Tokenization and stopword removal happen before stemming.
"""

from collections import Counter


def consonants(word: str) -> list[bool]:
    """Classify characters: True for consonant, False for vowel.

    Initial y is a consonant.
    Otherwise, y reverses the previous character's classification.
    """

    flags = []

    for letter in word:
        if letter in "aeiou":
            flags.append(False)
        elif letter == "y":
            flags.append(True if not flags else not flags[-1])
        else:
            flags.append(True)

    return flags


def measure(word: str) -> int:
    """Return m: the number of vowel-to-consonant transitions."""

    flags = consonants(word)

    return sum(
        not left and right
        for left, right in zip(flags, flags[1:])
    )


def contains_vowel(word: str) -> bool:
    """Implement *v*: check whether the candidate stem contains a vowel."""

    return any(not flag for flag in consonants(word))


def ends_double_consonant(word: str) -> bool:
    """Implement *d*: check for a repeated final consonant."""

    return (
        len(word) >= 2
        and word[-1] == word[-2]
        and consonants(word)[-1]
    )


def ends_cvc(word: str) -> bool:
    """Implement *o*: final CVC, excluding final w, x, and y."""

    return (
        len(word) >= 3
        and consonants(word)[-3:] == [True, False, True]
        and word[-1] not in "wxy"
    )


def step1a(word: str) -> str:
    """Handle plural endings, considering the longest suffix first."""

    rules = (
        ("sses", "ss"),
        ("ies", "i"),
        ("ss", "ss"),
        ("s", ""),
    )

    for suffix, replacement in rules:
        if word.endswith(suffix):
            return word[:-len(suffix)] + replacement

    return word


def step1b(word: str) -> str:
    """Handle EED, ED, and ING, with cleanup after ED/ING removal."""

    # EED must be checked before ED.
    if word.endswith("eed"):
        stem = word[:-3]

        if measure(stem) > 0:
            return stem + "ee"

        # Do not try ED after a failed EED condition.
        return word

    for suffix in ("ed", "ing"):
        if word.endswith(suffix):
            stem = word[:-len(suffix)]

            if not contains_vowel(stem):
                return word

            # Cleanup runs only after ED or ING was removed.
            if stem.endswith(("at", "bl", "iz")):
                return stem + "e"

            if ends_double_consonant(stem):
                if stem[-1] not in "lsz":
                    return stem[:-1]
                return stem

            if measure(stem) == 1 and ends_cvc(stem):
                return stem + "e"

            return stem

    return word


def step1c(word: str) -> str:
    """Replace final Y with I if the preceding stem contains a vowel."""

    if word.endswith("y"):
        stem = word[:-1]

        if contains_vowel(stem):
            return stem + "i"

    return word


def step1(word: str) -> str:
    """Apply Steps 1a, 1b, and 1c in order."""

    word = step1a(word)
    word = step1b(word)
    word = step1c(word)

    return word


# Original Porter Step 2 uses ABLI -> ABLE.
STEP2_RULES = (
    ("ational", "ate"),
    ("tional", "tion"),
    ("enci", "ence"),
    ("anci", "ance"),
    ("izer", "ize"),
    ("abli", "able"),
    ("alli", "al"),
    ("entli", "ent"),
    ("eli", "e"),
    ("ousli", "ous"),
    ("ization", "ize"),
    ("ation", "ate"),
    ("ator", "ate"),
    ("alism", "al"),
    ("iveness", "ive"),
    ("fulness", "ful"),
    ("ousness", "ous"),
    ("aliti", "al"),
    ("iviti", "ive"),
    ("biliti", "ble"),
)

STEP3_RULES = (
    ("icate", "ic"),
    ("ative", ""),
    ("alize", "al"),
    ("iciti", "ic"),
    ("ical", "ic"),
    ("ful", ""),
    ("ness", ""),
)

STEP4_SUFFIXES = (
    "al",
    "ance",
    "ence",
    "er",
    "ic",
    "able",
    "ible",
    "ant",
    "ement",
    "ment",
    "ent",
    "ion",
    "ou",
    "ism",
    "ate",
    "iti",
    "ous",
    "ive",
    "ize",
)


def apply_measured_rules(word, rules, minimum_measure=0):
    """Apply the longest matching suffix if m > minimum_measure.

    If its condition fails, return the word unchanged.
    Do not try a shorter suffix.
    """

    ordered_rules = sorted(
        rules,
        key=lambda rule: len(rule[0]),
        reverse=True,
    )

    for suffix, replacement in ordered_rules:
        if word.endswith(suffix):
            stem = word[:-len(suffix)]

            if measure(stem) > minimum_measure:
                return stem + replacement

            return word

    return word


def step2(word: str) -> str:
    """Simplify a Step 2 suffix when its candidate stem has m > 0."""

    return apply_measured_rules(word, STEP2_RULES, minimum_measure=0)


def step3(word: str) -> str:
    """Simplify a Step 3 suffix when its candidate stem has m > 0."""

    return apply_measured_rules(word, STEP3_RULES, minimum_measure=0)


def step4(word: str) -> str:
    """Remove one suffix when its candidate stem has m > 1.

    ION also requires the remaining stem to end in S or T.
    """

    for suffix in sorted(STEP4_SUFFIXES, key=len, reverse=True):
        if word.endswith(suffix):
            stem = word[:-len(suffix)]

            if (
                measure(stem) > 1
                and (
                    suffix != "ion"
                    or stem.endswith(("s", "t"))
                )
            ):
                return stem

            # A failed longest match ends this step.
            return word

    return word


def step5a(word: str) -> str:
    """Remove final E when the measure and CVC conditions allow it."""

    if word.endswith("e"):
        stem = word[:-1]
        m = measure(stem)

        if m > 1 or (m == 1 and not ends_cvc(stem)):
            return stem

    return word


def step5b(word: str) -> str:
    """Reduce final LL to L when the word has m > 1."""

    if (
        word.endswith("ll")
        and ends_double_consonant(word)
        and measure(word) > 1
    ):
        return word[:-1]

    return word


def porter_stem(word: str) -> str:
    """Apply the complete original Porter sequence once."""

    word = step1(word)
    word = step2(word)
    word = step3(word)
    word = step4(word)
    word = step5a(word)
    word = step5b(word)

    return word


def s_stem(word: str) -> str:
    """Apply Harman's S-stemmer to a lowercase token.

    Use the first rule whose suffix and exception conditions qualify.
    This light stemmer handles plural endings only.
    """

    # Rule 1: IES -> Y, except EIES or AIES.
    if word.endswith("ies") and not word.endswith(("eies", "aies")):
        return word[:-3] + "y"

    # Rule 2: ES -> E, except AES, EES, or OES.
    if word.endswith("es") and not word.endswith(("aes", "ees", "oes")):
        return word[:-1]

    # Rule 3: remove S, except US or SS.
    if word.endswith("s") and not word.endswith(("us", "ss")):
        return word[:-1]

    return word


def stem_collection(documents, stem):
    """Stem documents, caching each distinct word's result.

    Arguments:
        documents: {document_id: [tokens]}
        stem: a function such as porter_stem or s_stem

    Returns:
        stemmed: {document_id: [stems]}
        before: Counter of original token occurrences
        after: Counter of stem occurrences
        cache: {original_word: stem}

    The input documents are not modified.
    """

    # One cache is shared across all documents in this collection.
    cache = {}
    stemmed = {}
    before, after = Counter(), Counter()

    for doc_id, terms in documents.items():
        result = []

        for word in terms:
            # Compute each distinct word's stem only once.
            if word not in cache:
                cache[word] = stem(word)

            # Preserve order and repeated occurrences.
            result.append(cache[word])

        # Preserve original IDs, including empty documents.
        stemmed[doc_id] = result

        before.update(terms)
        after.update(result)

    return stemmed, before, after, cache